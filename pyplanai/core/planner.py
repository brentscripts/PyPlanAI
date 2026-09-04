from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from .db import Database
from .models import BlockStatus, Task, TaskStatus, TimeBlock
from .parser import parse_week_file
from .config import DEFAULT_DB_PATH

class PyPlanCore:
    def __init__(self,db: Optional[Database] = None):
        self.db = db or Database()

    def ingest_file(self,path: str | Path) -> int:
        source_week = datetime.now().strftime("%Y-%m-%d")
        tasks = parse_week_file(path, source_week=source_week)
        for task in tasks:
            self.db.add_task(task)
        return len(tasks)
