from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

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

    def _init_schema(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript(SCHEMA)
        conn.commit()
        conn.close()
        
        