from __future__ import annotations

import sqlite3
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from .models import BlockStatus, Task, TaskStatus, TimeBlock

from .config import DEFAULT_DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    notes TEXT DEFAULT '',
    priority INTEGER DEFAULT 3,
    status TEXT DEFAULT 'pending',
    source_week TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_date TEXT DEFAULT '',
    start_time TEXT DEFAULT '',
    end_time TEXT DEFAULT '',
    summary_goal TEXT DEFAULT '',
    pomodoro_rhythm TEXT DEFAULT '',
    action_cue TEXT DEFAULT '',
    task_id INTEGER,
    status TEXT DEFAULT 'scheduled',
    created_at TEXT DEFAULT (datetime('now')),
    notified TEXT DEFAULT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
"""

class Database:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def add_task(self, task: Task) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO tasks (title, notes, priority, status, source_week)
                    VALUES (?, ?, ?, ?, ?)""",
                (task.title, task.notes, task.priority, task.status.value, task.source_week),
            )
            return cur.lastrowid

    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            notes=row["notes"],
            priority=row["priority"],
            status=TaskStatus(row["status"]),
            source_week=row["source_week"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
    
    def get_active_tasks(self) -> list[Task]:
        with self._connect() as conn:
            cur = conn.execute(
                """SELECT * FROM tasks WHERE status IN (?, ?) 
                    order by priority asc""",
                (TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value),
            )
            rows = cur.fetchall()
            return [self._row_to_task(r) for r in rows]  

    def update_task_status(self, task_id: int, new_status: TaskStatus) -> None:
        with self._connect() as conn:
            conn.execute(
                """UPDATE tasks SET status = ? WHERE id = ?""",
                (new_status.value, task_id),
            )

    def add_block(self, block: TimeBlock) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO blocks (source_date, start_time, end_time, summary_goal,
                    pomodoro_rhythm, action_cue, task_id, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (block.source_date, block.start_time, block.end_time, block.summary_goal,
                    block.pomodoro_rhythm, block.action_cue, block.task_id, block.status.value),
            )
            return cur.lastrowid

    @staticmethod
    def _row_to_block(row: sqlite3.Row) -> TimeBlock:
        return TimeBlock(
            id=row["id"],
            source_date=row["source_date"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            summary_goal=row["summary_goal"],
            pomodoro_rhythm=row["pomodoro_rhythm"],
            action_cue=row["action_cue"],
            task_id=row["task_id"],
            status=BlockStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            notified=datetime.fromisoformat(row["notified"]) if row["notified"] else None,
        )

    def get_blocks_by_date(self, source_date: str) -> list[TimeBlock]:
        with self._connect() as conn:
            cur = conn.execute(
                """SELECT * FROM blocks WHERE source_date = ?""",
                (source_date,),
            )
            rows = cur.fetchall()
            return [self._row_to_block(r) for r in rows]

    def get_block(self, block_id: int) -> Optional[TimeBlock]:
        with self._connect() as conn:
            cur = conn.execute(
                """SELECT * FROM blocks WHERE id = ?""",
                (block_id,),
            )
            row = cur.fetchone()
            return self._row_to_block(row) if row else None

    def update_block_status(self, block_id: int, new_status: BlockStatus) -> None:
        with self._connect() as conn:
            conn.execute(
                """UPDATE blocks SET status = ? WHERE id = ?""",
                (new_status.value, block_id),
            )

    def update_block_notified(self, block_id: int, notified_time: datetime) -> None:
        with self._connect() as conn:
            conn.execute(
                """UPDATE blocks SET notified = ? WHERE id = ?""",
                (notified_time.isoformat(), block_id),
            )

    def mark_notified(self, block_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                """UPDATE blocks SET status = ?, notified = ? WHERE id = ?""",
                (BlockStatus.NOTIFIED.value, datetime.now().isoformat(), block_id),
            )

    def reschedule_block(self, block_id: int, new_start_time: str, new_end_time: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """UPDATE blocks SET start_time = ?, end_time = ?, status = ? WHERE id = ?""",
                (new_start_time, new_end_time, BlockStatus.SCHEDULED.value, block_id),
            )

    def clear_blocks_for_date(self, source_date: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM blocks WHERE source_date = ?", (source_date,))