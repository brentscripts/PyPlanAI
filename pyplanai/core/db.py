from __future__ import annotations

import sqlite3
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from .models import BlockStatus, Task, TaskStatus, TimeBlock

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

DEFAULT_DB_PATH = Path.home() / ".pyplanai" / "pyplanai.db"

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