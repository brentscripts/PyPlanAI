from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date, time
from enum import Enum
from typing import Optional

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    SKIPPED = "skipped"

@dataclass
class Task:
    id: Optional[int]
    title: str
    notes: str = ""
    priority: int = 3 #1 (highest) to 5 (lowest)
    status: TaskStatus = TaskStatus.PENDING
    source_week: str = "" # e.g. "2026-08-24" (the Sunday it was ingested)
    created_at: datetime = field(default_factory=datetime.now)

class BlockStatus(str, Enum):
    SCHEDULED = "scheduled"
    NOTIFIED = "notified"
    ACTIVE = "active"
    DONE = "done"
    SKIPPED = "skipped"
    PUSHED = "pushed"  # Moved to a different time block

@dataclass
class TimeBlock:
    id: Optional[int]
    source_date: str = ""
    start_time: str = ""
    end_time: str = ""
    summary_goal: str = ""
    pomodoro_rhythm: str = ""  # e.g., "25-5" for 25 minutes work, 5 minutes break
    action_cue: str = ""
    task_id: Optional[int] = None  # Link to a Task by its ID
    status: BlockStatus = BlockStatus.SCHEDULED
    created_at: datetime = field(default_factory=datetime.now)
    notified: Optional[datetime] = None  # Timestamp when the user was notified