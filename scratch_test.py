from __future__ import annotations

import os

from pyplanai.core.db import Database
from pyplanai.core.planner import PyPlanCore


class FakeLLMClient:
    def generate_blueprint(self, date_str, tasks):
        return [
            {
                "start_time": "09:00",
                "end_time": "09:50",
                "summary_goal": "Deep work",
                "pomodoro_rhythm": "50 min focus / 10 min break",
                "action_cue": "Open the document",
                "task_title": tasks[0]["title"] if tasks else None,
            },
            {
                "start_time": "10:00",
                "end_time": "10:50",
                "summary_goal": "Second block",
                "pomodoro_rhythm": "50 min focus / 10 min break",
                "action_cue": "Pick up where you left off",
                "task_title": tasks[1]["title"] if len(tasks) > 1 else None,
            },
        ]


TEST_DB_PATH = "/tmp/pyplanai_test.db"
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)

db = Database(db_path=TEST_DB_PATH)
ppc = PyPlanCore(db=db, llm=FakeLLMClient())

count = ppc.ingest_file("./test_week.md")
print("ingested:", count)

blocks = ppc.generate_daily_blueprint()
print("blocks created:", len(blocks))
for b in blocks:
    print(b.id, b.task_id, b.start_time, "-", b.end_time, "|", b.summary_goal)

    
    