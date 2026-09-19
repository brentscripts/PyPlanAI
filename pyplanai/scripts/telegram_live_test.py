from __future__ import annotations

import os

from pyplanai.core.db import Database
from pyplanai.core.planner import PyPlanCore
from pyplanai.adapters.telegram_bot import build_command_bot
from pyplanai.core.config import TELEGRAM_BOT_TOKEN

TEST_DB_PATH = "/tmp/pyplanai_test.db"
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)

db = Database(db_path=TEST_DB_PATH)
core = PyPlanCore(db=db)

core.ingest_file("./test_week.md")
blocks = core.generate_daily_blueprint()
print(f"Generated {len(blocks)} blocks. Try commands like:")
for b in blocks[:3]:
    print(f"  /skip {b.id}")
    print(f"  /later {b.id} 15")

app = build_command_bot(core, TELEGRAM_BOT_TOKEN)
print("\nBot is now listening. Send /skip or /later from Telegram. Ctrl+C to stop.")
app.run_polling()