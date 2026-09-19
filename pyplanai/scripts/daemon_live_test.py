from __future__ import annotations

import os
from datetime import datetime, timedelta

from pyplanai.core.db import Database
from pyplanai.core.models import TimeBlock

TEST_DB_PATH = "/tmp/pyplanai_test.db"
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)

db = Database(db_path=TEST_DB_PATH)

now = datetime.now()
soon = now + timedelta(minutes=1)

block = TimeBlock(
    id=None,
    source_date=now.strftime("%Y-%m-%d"),
    start_time=soon.strftime("%H:%M"),
    end_time=(soon + timedelta(minutes=30)).strftime("%H:%M"),
    summary_goal="Daemon live test",
    pomodoro_rhythm="test",
    action_cue="Confirm the notification fired",
    task_id=None,
)
block.id = db.add_block(block)
print(f"Created block #{block.id} starting at {block.start_time}")