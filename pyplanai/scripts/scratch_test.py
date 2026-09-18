from __future__ import annotations

import os

from pyplanai.core.db import Database
from pyplanai.core.planner import PyPlanCore

TEST_DB_PATH = "/tmp/pyplanai_test.db"
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)

db = Database(db_path=TEST_DB_PATH)
ppc = PyPlanCore(db=db)  # no llm= passed — this will now lazily create a real GroqPlannerClient

count = ppc.ingest_file("./test_week.md")
print("ingested:", count)

blocks = ppc.generate_daily_blueprint()
print("blocks created:", len(blocks))
for b in blocks:
    print(b.id, b.task_id, b.start_time, "-", b.end_time, "|", b.summary_goal, "|", b.action_cue)

print("\n--- Testing skip_block ---")
skipped = ppc.skip_block(blocks[0].id)
print("block status:", skipped.status)
active = ppc.db.get_active_tasks()
print("still-active task count:", len(active))

print("\n--- Testing push_block_later ---")
pushed = ppc.push_block_later(blocks[1].id, 15)
print("original:", blocks[1].start_time, "-", blocks[1].end_time)
print("pushed:  ", pushed.start_time, "-", pushed.end_time)
print("pushed status:", pushed.status)