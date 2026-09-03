# PyPlanAI

An ADHD-friendly, McConaughey-flavored personal planning agent. Give it your
rough weekly tasks, and it generates a daily Morning Blueprint of Pomodoro'd
Time Blocks, then pings you 2 minutes before each one via desktop
notification and Telegram — with zero-guilt `/skip` and `/later` escape
hatches.

## Architecture

Decoupled core + thin adapters, so every frontend shares one brain:

```
pyplanai/
├── core/           # PyPlanCore — all business logic, no frontend code
│   ├── models.py       Task, TimeBlock dataclasses
│   ├── db.py            SQLite persistence
│   ├── llm.py             Groq client wrapper
│   ├── parser.py           Weekly file -> Task list
│   ├── planner.py           PyPlanCore: the API every adapter calls
│   └── prompts/system_prompt.md
├── adapters/       # thin shells, call PyPlanCore only
│   ├── cli.py           ingest / plan / status / skip / later
│   ├── telegram_bot.py    notifications + /skip /later /status
│   └── notify_desktop.py   notify-send wrapper
└── daemon.py       # runs the scheduler loop + Telegram bot together
```

## Setup

```bash
cd pyplanai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: add your GROQ_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
```

Get a free Groq API key at https://console.groq.com/keys.

Create a Telegram bot by messaging **@BotFather** on Telegram, `/newbot`,
follow the prompts, and copy the token it gives you. Message your new bot
once, then visit `https://api.telegram.org/bot<TOKEN>/getUpdates` to find
your `chat_id`.

## Weekly task file format

Write a plain Markdown/text file, forgiving on purpose:

```markdown
# Week of 2026-08-31

- Finish PyPlanAI core layer !1
- Call dentist to reschedule !3
- Draft blog post
  notes: pull from the March draft, keep it under 800 words
- Groceries !2
```

`!N` sets priority (1 = highest, 5 = lowest, default 3). An indented
`notes:` line attaches notes to the task above it.

## Usage

```bash
# Sunday night (and any night): ingest your task file
python -m pyplanai.adapters.cli ingest week.md

# Each morning: generate today's blueprint
python -m pyplanai.adapters.cli plan

# Check status any time
python -m pyplanai.adapters.cli status

# Manually skip or push a block (normally done via Telegram reply)
python -m pyplanai.adapters.cli skip 3
python -m pyplanai.adapters.cli later 3 30
```

Run the daemon in the background so notifications fire automatically:

```bash
python -m pyplanai.daemon
```

Leave it running (e.g. in a `tmux`/`screen` session, or as a `systemd
--user` service — see below) and it will:
- Poll every 30 seconds for blocks starting within 2 minutes.
- Fire a desktop notification (`notify-send`) **and** a Telegram message.
- Listen for `/skip <id>` and `/later <id> [minutes]` replies in Telegram.

## Running as a systemd user service (optional)

Create `~/.config/systemd/user/pyplanai.service`:

```ini
[Unit]
Description=PyPlanAI daemon

[Service]
WorkingDirectory=/path/to/pyplanai
ExecStart=/path/to/pyplanai/venv/bin/python -m pyplanai.daemon
Restart=on-failure

[Install]
WantedBy=default.target
```

Then:

```bash
systemctl --user daemon-reload
systemctl --user enable --now pyplanai.service
``

## Roadmap

- Local web dashboard reusing the same `PyPlanCore` API for rich visual
  planning views.
- Docker packaging once the core is stable.
- Historical stats (skip rate by day/time, streaks) using the same SQLite
  data already being collected.
