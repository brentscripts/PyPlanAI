# PyPlanAI

An ADHD-friendly, McConaughey-flavored personal planning agent. Give it your
day's rough tasks, and it generates a Morning Blueprint of Pomodoro'd Time
Blocks, then pings you 2 minutes before each one via desktop notification
and Telegram — with zero-guilt `/skip`, `/later`, and `/complete` escape
hatches.

## Project Status & Intent

This codebase is a personal project. To preserve the integrity of this work as an individual evaluation piece:
* External issues and pull requests are disabled/ignored.
* The code is public for **viewing and review purposes only**. 
Please refer to the `LICENSE` file regarding permissions and restrictions on reuse.

## Architecture

Decoupled core + thin adapters, so every frontend shares one brain — no
business logic is ever duplicated between the CLI, the Telegram bot, or
any future frontend (e.g. a web dashboard).

```
pyplanai/
├── core/                    # PyPlanCore — all business logic, zero frontend code
│   ├── models.py             Task, TimeBlock dataclasses; TaskStatus, BlockStatus enums
│   ├── db.py                  SQLite persistence layer (schema + CRUD)
│   ├── config.py                Centralized settings, reads .env
│   ├── parser.py                Daily/weekly Markdown/text file -> list[Task]
│   ├── llm.py                    Groq API client wrapper, with retry on parse failure
│   ├── planner.py                  PyPlanCore: the single API every adapter calls
│   └── prompts/
│       └── system_prompt.md          McConaughey persona + blueprint instructions
├── adapters/                # thin shells — call PyPlanCore only, no logic of their own
│   ├── cli.py                 ingest / plan / status / skip / later / complete / add / complete-task / skip-task
│   ├── telegram_bot.py          notifications + /skip /later /complete handlers
│   └── notify_desktop.py          notify-send wrapper for Ubuntu desktop popups
├── daemon.py                # background process: scheduler loop + Telegram polling together
scripts/
├── telegram_live_test.py    # runs the command bot standalone, live, for manual command testing
└── daemon_live_test.py      # seeds one block ~1 min out, for testing the daemon's notification firing
scratch_test.py               # fast, mocked end-to-end test of PyPlanCore (no real API calls)
llm_live_test.py              # standalone sanity check of GroqPlannerClient against the real API
test_week.md                  # sample task file used by the tests above
pyproject.toml                # packaging + pyplanai console script entry point
requirements.txt
.env.example
README.md
```

## How it works

1. **Each night:** you write/update a rough Markdown task file describing
   *tomorrow's* tasks (see below on why daily beats weekly for this app).
   Run `pyplanai ingest week.md` to parse it and store tasks in SQLite.
2. **Each morning (or the night before):** run `pyplanai plan` to generate
   the day's Morning Blueprint — Groq turns your active tasks into a
   schedule of Pomodoro'd Time Blocks, each stored in SQLite.
3. **The daemon runs continuously in the background** (`python -m
   pyplanai.daemon`), checking every 30 seconds for blocks starting within
   2 minutes. When one's due, it fires a **Two-Minute Warning** — both a
   desktop notification (`notify-send`) and a Telegram message — naming the
   exact first, lowest-friction action step.
4. **Reply `/skip <id>`, `/later <id> [minutes]`, or `/complete <id>`** in
   Telegram (or via CLI) to zero-guilt skip a block, push it later, or mark
   it done — with the daemon listening for replies the whole time it's
   also watching the clock.
5. **Something comes up mid-day?** `pyplanai add "task title" --priority 2`
   adds it on the spot, no file editing required (it won't appear in
   today's already-generated blueprint until you re-run `plan`, which
   regenerates the whole remaining day).

### Daily vs. weekly files

The app has no concept of "which day of the week" a task belongs to —
`generate_daily_blueprint` schedules *every currently active task* into
"today," regardless of what day it was written for. Because of that,
**one file per day works far better than one file for the whole week**:
it keeps "active tasks" naturally scoped to roughly a day's worth, avoids
accidentally scheduling next Tuesday's tasks into today, and — as a real
bonus for ADHD-focused planning — forces a nightly reflection: what
actually got done today, and what's realistic for tomorrow. A full week
planned in advance tends to go stale fast once real life happens.

## Setup

```bash
git clone <your-repo-url>
cd PyPlanAI
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env
# edit .env: add GROQ_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
```

Get a free Groq API key at https://console.groq.com/keys. As of this
writing, `openai/gpt-oss-120b` is the model in use — Groq's available free
models change periodically; check https://console.groq.com/docs/models if
`llm.py` ever reports a model-not-found error.

Create a Telegram bot via **@BotFather** on Telegram (`/newbot`), copy the
token it gives you. Message your new bot once, then visit
`https://api.telegram.org/bot<TOKEN>/getUpdates` to find your `chat_id`.
If you ever suspect your bot token has leaked (e.g. pasted somewhere it
shouldn't have been), revoke and regenerate it via BotFather's "API
Token" menu, then update `.env` — `config.py`'s `load_dotenv(override=True)`
ensures the new value actually takes effect over any stale cached one.

### Local testing without touching real data

Set `PYPLANAI_DB_PATH` in `.env` to a temp path so test runs never pollute
your real task/schedule history:

```
PYPLANAI_DB_PATH=/tmp/pyplanai_test.db
```

Remove or comment out that line (or point it at
`~/.pyplanai/pyplanai.db`) to use the real database.

**No deduplication on ingest yet** — running `pyplanai ingest` twice
against the same file's content will double up every task. If you need to
retry an ingest after an error partway through, clear the database first:
`rm ~/.pyplanai/pyplanai.db` (or the temp path, if testing).

## Task file format

Write a plain Markdown/text file, forgiving on purpose — no rigid syntax
to fight against at night:

```markdown
# 2026-09-20

- Wake up, coffee and time with God from 6:00 AM to 7:00 AM !1
- Resume Basement window install !1
  notes: Sunrise is 6:30 AM, start at 7:00 AM and work until 9:00 AM
- Get ready for Church !2
- Personal Finances from 3:00 PM to 5:00 PM !4
  notes: Pay bills and work on personal finance application
```

- Each `- ` line starts a new task.
- `!N` sets priority — **1 through 5 only** (1 highest, 5 lowest); anything
  outside that range (e.g. `!6`) won't match and silently falls back to
  the default priority of `3`, with the marker left in the title. Stick to
  1–5.
- An indented `notes:` line right after a task attaches notes to it.
- Lines starting with `#` are ignored (headers/comments).

## Usage

```bash
# Ingest your day's file
pyplanai ingest week.md

# Generate today's blueprint
pyplanai plan

# See active tasks and today's blocks
pyplanai status

# Add a single task on the fly, no file editing needed
pyplanai add "Quick errand that came up" --priority 2

# Block-level actions (need a block id from `plan`/`status`)
pyplanai skip 3
pyplanai later 3 15
pyplanai complete 3

# Task-level actions (work even without a generated block)
pyplanai complete-task 7
pyplanai skip-task 7
```

Run the daemon so notifications fire automatically:

```bash
python -m pyplanai.daemon
```

Leave it running (e.g. in `tmux`/`screen`, or as a `systemd --user`
service) and it will poll every 30 seconds, fire the Two-Minute Warning via
desktop + Telegram, and listen for `/skip`/`/later`/`/complete` replies the
whole time.

### Running as a systemd user service (recommended for daily use)

Create `~/.config/systemd/user/pyplanai.service`:

```ini
[Unit]
Description=PyPlanAI daemon
After=network.target

[Service]
WorkingDirectory=/path/to/PyPlanAI
ExecStart=/path/to/PyPlanAI/venv/bin/python -m pyplanai.daemon
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now pyplanai.service
```

Check it's running: `systemctl --user status pyplanai.service`. Watch logs
live: `journalctl --user -u pyplanai.service -f`.

### Verifying and monitoring the daemon

Confirm it's actually running:
```bash
systemctl --user status pyplanai.service
```
Look for `Active: active (running)`. `enabled` in the `Loaded` line confirms
it'll start automatically on future logins/boots.

Confirm it survives logout/reboot, not just the current session (without
this, the service can stop when you log out and won't restart until you
log back in):
```bash
loginctl enable-linger $USER
loginctl show-user $USER | grep Linger
```
Should show `Linger=yes`.

Watch what it's doing in real time (useful for confirming a notification
actually fired, or diagnosing an error):
```bash
journalctl --user -u pyplanai.service -f
```
`-f` follows the log live, like `tail -f`. `Ctrl+C` stops watching without
stopping the service itself.

Restart it after a code change (systemd won't pick up edits to
`pyplanai/` automatically — the running process has the old code loaded
in memory until restarted):
```bash
systemctl --user restart pyplanai.service
```

Stop it entirely:
```bash
systemctl --user stop pyplanai.service
```

### Running on a separate machine (e.g. an OrangePi)

SQLite is a local file, not a network service — the CLI, the task file,
and the daemon all need to live on the **same machine** as the database
(`~/.pyplanai/pyplanai.db`). If the daemon runs on a separate always-on
box, you'll `ssh` into it to edit the task file and run `ingest`/`plan`,
or sync the file over some other way. The planned web dashboard (see
Roadmap) is the real fix for this — a browser UI reachable from any
device, with no SSH required.

## Known Issues

- **No deduplication on `ingest_file`.** Re-running `ingest` against the
  same file's content adds duplicate tasks every time. Clear the database
  (`rm ~/.pyplanai/pyplanai.db`) before retrying a failed ingest.
- **Tasks have no day-of-week awareness.** `get_active_tasks()` and
  `generate_daily_blueprint` treat every `PENDING` task as a flat, dateless
  pool — there's no way to say "this task belongs to tomorrow, not today."
  In practice this means: if you ingest and plan for tomorrow
  (`pyplanai plan --tomorrow`) while any of today's tasks are still
  `PENDING`, they'll bleed into tomorrow's blueprint alongside tomorrow's
  fresh tasks. Workaround: fully resolve today (mark each remaining task
  `complete-task` or `skip-task` as it actually happens, or honestly
  `skip-task` anything that won't get done) before ingesting and planning
  for the next day. The real fix is tagging tasks with a target date and
  filtering `get_active_tasks()`/blueprint generation by it — see Roadmap.
  
## Roadmap

- **Smarter re-planning on skip/later** — instead of blindly shifting one
  block's time, re-call the LLM with the day's remaining tasks so the rest
  of the schedule reflows sensibly around a skip or delay, rather than
  risking overlapping blocks.
- **Local web dashboard** reusing the same `PyPlanCore` API for rich visual
  planning views, and to solve remote (e.g. OrangePi) access cleanly.
- **Natural-language commands** — text the bot freely ("push everything
  back an hour", "lighten up today") and have the LLM interpret intent and
  call the right `PyPlanCore` methods, instead of requiring exact
  `/command <id>` syntax.
- **Pattern reflection / coaching** — periodic LLM-generated insight from
  accumulated skip/complete/reschedule history (e.g. recurring skip
  patterns by time of day), in the spirit of the app's original
  ADHD-executive-function-support design.
- **Google Calendar integration** — push generated blocks as calendar
  events, as a complementary notification channel alongside desktop and
  Telegram (not a replacement for PyPlanAI's LLM-driven planning).
- Docker packaging.
- Historical stats (skip rate by day/time, streaks) using the same SQLite
  data already being collected.
- Deduplication on `ingest_file` for re-ingesting the same file safely.
- Day-of-week aware scheduling, if a genuine weekly (rather than daily)
  workflow is wanted later.

## Progress log

- [x] **models.py** — `Task`, `TimeBlock` dataclasses, `TaskStatus`/`BlockStatus` enums. Tested.
- [x] **db.py** — SQLite schema (`tasks`, `blocks`), full CRUD for both. Tested.
- [x] **parser.py** — regex-based file parser, priority (1–5) + notes extraction. Tested.
- [x] **config.py** — centralized settings via `.env`, `PYPLANAI_DB_PATH` override, override-safe `load_dotenv`.
- [x] **planner.py** — `PyPlanCore`: ingest, generate blueprint (task-linked), skip/complete (block + task level, direct), push later, upcoming-notification lookup, ad-hoc task add. Tested.
- [x] **llm.py** — real Groq client, JSON parsing with fence-stripping, retry-on-failure, and a higher token ceiling for full real-world days. Tested against live API with real multi-task days.
- [x] **adapters/cli.py** — `ingest`/`plan`/`status`(tasks+blocks)/`skip`/`later`/`complete`/`add`/`complete-task`/`skip-task`, installed as a real `pyplanai` command. Tested.
- [x] **adapters/notify_desktop.py** — `notify-send` wrapper. Tested.
- [x] **adapters/telegram_bot.py** — send + `/skip`/`/later`/`/complete` command handlers. Tested live.
- [x] **daemon.py** — scheduler loop + Telegram polling running concurrently via asyncio, deployed as a systemd user service. Tested live, end to end, against a real full day.
- [x] **Date-targeted planning** — `pyplanai plan --tomorrow` generates
  and stamps blocks with the next day's date, so planning the night before
  actually works with the daemon correctly finding them the following
  morning. Fixes the same-day-only limitation discovered during first
  real-world use.



