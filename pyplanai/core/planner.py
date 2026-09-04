from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from .db import Database
from .models import BlockStatus, Task, TaskStatus, TimeBlock
from .parser import parse_week_file
from .config import DEFAULT_DB_PATH

class PyPlanCore:
    def __init__(self,db: Optional[Database] = None, llm = None):
        self.db = db or Database()
        self.llm = llm

    def ingest_file(self,path: str | Path) -> int:
        source_week = datetime.now().strftime("%Y-%m-%d")
        tasks = parse_week_file(path, source_week=source_week)
        for task in tasks:
            self.db.add_task(task)
        return len(tasks)

    def generate_daily_blueprint(self):
            today_str = datetime.now().strftime("%Y-%m-%d")
            active_tasks = self.db.get_active_tasks()
            if not active_tasks:
                return []
            task_dicts = [{"title": task.title, "priority": task.priority, "notes": task.notes} for task in active_tasks]
            block_dicts = self.llm.generate_blueprint(today_str, task_dicts)
            saved_blocks = []
            for block_dict in block_dicts:
                block = TimeBlock(
                    id=None,
                    source_date=today_str,
                    start_time=block_dict["start_time"],
                    end_time=block_dict["end_time"],
                    summary_goal=block_dict["summary_goal"],
                    pomodoro_rhythm=block_dict["pomodoro_rhythm"],
                    action_cue=block_dict["action_cue"],
                    task_id=None,
                )
                block.id = self.db.add_block(block)
                saved_blocks.append(block)
            return saved_blocks
