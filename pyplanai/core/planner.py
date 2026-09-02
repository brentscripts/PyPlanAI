from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from .db import Database
from .models import BlockStatus, Task, TaskStatus, TimeBlock

class PyPlanCore:
    def __init__(self,db: Optional[Database] = None):
        self.db = db or Database()
