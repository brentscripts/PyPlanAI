# PyPlanAI

An ADHD-friendly, McConaughey-flavored personal planning agent. Give it your
rough weekly tasks, and it generates a daily Morning Blueprint of Pomodoro'd
Time Blocks, then pings you 2 minutes before each one via desktop
notification and Telegram — with zero-guilt `/skip` and `/later` escape
hatches.

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
│   ├── parser.py                Weekly Markdown/text file -> list[Task]
│   ├── llm.py                    Groq API client wrapper
│   ├── planner.py                  PyPlanCore: the single API every adapter calls
│   └── prompts/
│       └── system_prompt.md          McConaughey persona + blueprint instructions
├── adapters/                # thin shells — call PyPlanCore only, no logic of their own
│   ├── cli.py                 ingest / plan / status / skip / later commands
│   ├── telegram_bot.py          notifications + /skip /later handlers
│   └── notify_desktop.py          notify-send wrapper for Ubuntu desktop popups
├── daemon.py                # background process: scheduler loop + Telegram polling together
scripts/
├── telegram_live_test.py    # runs the command bot standalone, live, for manual /skip /later testing
└── daemon_live_test.py      # seeds one block ~1 min out, for testing the daemon's notification firing
scratch_test.py               # fast, mocked end-to-end test of PyPlanCore (no real API calls)
llm_live_test.py              # standalone sanity check of GroqPlannerClient against the real API
test_week.md                  # sample weekly task file used by the tests above
pyproject.toml                # packaging + pyplanai console script entry point
requirements.txt
.env.example
README.md
```

## How it works

1. **Sunday night (and any night):** you write/update a rough Markdown task
   file. Run `pyplanai ingest week.md` to parse it and store tasks in SQLite.
2. **Each morning:** run `pyplanai plan` to generate today's Morning
   Blueprint — Groq turns your active tasks into a schedule of Pomodoro'd
   Time Blocks, each stored in SQLite.
3. **The daemon runs continuously in the background** (`python -m
   pyplanai.daemon`), checking every 30 seconds for blocks starting within
   2 minutes. When one's due, it fires a **Two-Minute Warning** — both a
   desktop notification (`notify-send`) and a Telegram message — naming the
   exact first, lowest-friction action step.
4. **Reply `/skip <id>` or `/later <id> [minutes]`** in Telegram (or via
   CLI) to zero-guilt skip a block or push it later, with the daemon
   listening for replies the whole time it's also watching the clock.

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

### Local testing without touching real data

Set `PYPLANAI_DB_PATH` in `.env` to a temp path so test runs never pollute
your real task/schedule history:

PYPLANAI_DB_PATH=/tmp/pyplanai_test.db

Remove or comment out that line (or point it at
`~/.pyplanai/pyplanai.db`) to use the real database.

## Weekly task file format

Write a plain Markdown/text file, forgiving on purpose — no rigid syntax
to fight on a Sunday night:

```markdown
# Week of 2026-08-31

- Finish PyPlanAI core layer !1
- Call dentist to reschedule !3
- Draft blog post
  notes: pull from the March draft, keep it under 800 words
- Groceries !2
```

- Each `- ` line starts a new task.
- `!N` (1–5, anywhere in the line) sets priority. Default is `3` if omitted.
- An indented `notes:` line right after a task attaches notes to it.
- Lines starting with `#` are ignored (headers/comments).

## Usage

```bash
# Ingest your weekly file (Sunday night, or any update)
pyplanai ingest week.md

# Generate today's blueprint
pyplanai plan

# Check today's block statuses
pyplanai status

# Manually skip or push a block (normally done via Telegram reply)
pyplanai skip 3
pyplanai later 3 15
```

Run the daemon so notifications fire automatically:

```bash
python -m pyplanai.daemon
```

Leave it running (e.g. in `tmux`/`screen`, or as a `systemd --user`
service) and it will poll every 30 seconds, fire the Two-Minute Warning via
desktop + Telegram, and listen for `/skip`/`/later` replies the whole time.

### Running as a systemd user service (optional)

Create `~/.config/systemd/user/pyplanai.service`:

```ini
[Unit]
Description=PyPlanAI daemon

[Service]
WorkingDirectory=/path/to/PyPlanAI
ExecStart=/path/to/PyPlanAI/venv/bin/python -m pyplanai.daemon
Restart=on-failure

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now pyplanai.service
```

## Roadmap

- Local web dashboard reusing the same `PyPlanCore` API for rich visual
  planning views.
- Docker packaging.
- Historical stats (skip rate by day/time, streaks) using the same SQLite
  data already being collected.
- Deduplication on `ingest_file` for re-ingesting the same week's file.

## Progress log

- [x] **models.py** — `Task`, `TimeBlock` dataclasses, `TaskStatus`/`BlockStatus` enums. Tested.
- [x] **db.py** — SQLite schema (`tasks`, `blocks`), full CRUD for both. Tested.
- [x] **parser.py** — regex-based weekly file parser, priority + notes extraction. Tested.
- [x] **config.py** — centralized settings via `.env`, `PYPLANAI_DB_PATH` override, override-safe `load_dotenv`.
- [x] **planner.py** — `PyPlanCore`: ingest, generate blueprint (task-linked), skip, push later, upcoming-notification lookup. Tested.
- [x] **llm.py** — real Groq client, JSON parsing with fence-stripping and error handling. Tested against live API.
- [x] **adapters/cli.py** — `ingest`/`plan`/`status`/`skip`/`later`, installed as a real `pyplanai` command. Tested.
- [x] **adapters/notify_desktop.py** — `notify-send` wrapper. Tested.
- [x] **adapters/telegram_bot.py** — send + `/skip`/`/later` command handlers. Tested live.
- [x] **daemon.py** — scheduler loop + Telegram polling running concurrently via asyncio. Tested live, end to end.