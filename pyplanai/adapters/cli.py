from __future__ import annotations

import argparse

from pyplanai.core.planner import PyPlanCore


def cmd_ingest(core: PyPlanCore, args: argparse.Namespace) -> None:
    count = core.ingest_file(args.file)
    print(f"Alright, alright, alright. Ingested {count} task(s) from {args.file}.")

def cmd_plan(core: PyPlanCore, args: argparse.Namespace) -> None:
    blocks = core.generate_daily_blueprint()
    if not blocks:
        print("No active tasks found, brother. Ingest a week file first")
        return
    print("\nToday's Morning Blueprint:\n")
    for b in blocks:
        print(f"[{b.start_time} - {b.end_time}] (#{b.id}): {b.summary_goal}")
        print(f"  Rhythm: {b.pomodoro_rhythm}")
        print(f"  Action: {b.action_cue}\n")

def cmd_status(core: PyPlanCore, args: argparse.Namespace) -> None:
    tasks = core.db.get_active_tasks()
    if not tasks:
        print("No active tasks found, brother. Ingest a week file first")
    else:
        print("Active Tasks:")
        for t in tasks:
            print(f" Task ID: {t.id}")
            print(f" Title: {t.title}")
            print(f" Status: {t.status}")

    blocks = core.get_today_blocks()
    if blocks:
        print("\nToday's Blocks:")
        for b in blocks:
            print(f" Block ID: {b.id} [{b.start_time}-{b.end_time}] {b.summary_goal} — {b.status}")

def cmd_skip(core: PyPlanCore, args: argparse.Namespace) -> None:
    skip = core.skip_block(args.block_id)
    if not skip:
        print(f"Id:{args.block_id} not found.")
    else:
        print(f"Skipped block id:{args.block_id}.")

def cmd_later(core: PyPlanCore, args: argparse.Namespace) -> None:
    later = core.push_block_later(args.block_id, args.minutes)
    if not later:
        print(f"Id:{args.block_id} not found.")
    else:
        print(f"Moved block id:{args.block_id} to {later.start_time} - {later.end_time}.") 

def cmd_complete(core: PyPlanCore, args: argparse.Namespace) -> None:
    block = core.complete_block(args.block_id)
    if not block:
        print(f"Id:{args.block_id} not found.")
    else:
        print(f"Completed block id:{args.block_id}. Green lights, brother.") 

def cmd_add(core: PyPlanCore, args: argparse.Namespace) -> None:
    task_id = core.add_task(args.title, priority=args.priority, notes=args.notes or "")
    print(f"Alright, alright, alright. Added task #{task_id}: {args.title}")

def cmd_complete_task(core: PyPlanCore, args: argparse.Namespace) -> None:
    core.complete_task(args.task_id)
    print(f"Task #{args.task_id} marked complete. Green lights, brother.")

def cmd_skip_task(core: PyPlanCore, args: argparse.Namespace) -> None:
    core.skip_task(args.task_id)
    print(f"Task #{args.task_id} skipped. Next green light's coming.")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pyplanai")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_ingest = subparsers.add_parser("ingest", help="Ingest a weekly task file")
    p_ingest.add_argument("file", help="Path to the week's Markdown/text file")
    p_ingest.set_defaults(func=cmd_ingest)

    p_plan = subparsers.add_parser("plan", help="Generate today's Morning Blueprint")
    p_plan.set_defaults(func=cmd_plan)

    p_status = subparsers.add_parser("status", help="Show status of active tasks")
    p_status.set_defaults(func=cmd_status)

    p_skip = subparsers.add_parser("skip", help="Skip a planned block")
    p_skip.add_argument("block_id", type=int, help="ID of the block to skip")
    p_skip.set_defaults(func=cmd_skip)

    p_later = subparsers.add_parser("later", help="Push a planned block later")
    p_later.add_argument("block_id", type=int, help="ID of the block to push later")
    p_later.add_argument("minutes", type=int, nargs="?", default=30, help="Minutes to push it later by (default 30)")
    p_later.set_defaults(func=cmd_later)

    p_complete = subparsers.add_parser("complete", help="Mark a block (and its task) as done")
    p_complete.add_argument("block_id", type=int, help="ID of the block to complete")
    p_complete.set_defaults(func=cmd_complete)

    p_add = subparsers.add_parser("add", help="Add a single task")
    p_add.add_argument("title", help="Task title")
    p_add.add_argument("--priority", type=int, default=3, help="Priority 1-5 (default 3)")
    p_add.add_argument("--notes", default="", help="Optional notes")
    p_add.set_defaults(func=cmd_add)

    p_complete_task = subparsers.add_parser("complete-task", help="Mark a task done directly")
    p_complete_task.add_argument("task_id", type=int)
    p_complete_task.set_defaults(func=cmd_complete_task)

    p_skip_task = subparsers.add_parser("skip-task", help="Mark a task skipped directly")
    p_skip_task.add_argument("task_id", type=int)
    p_skip_task.set_defaults(func=cmd_skip_task)

    return parser   


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    core = PyPlanCore()
    args.func(core, args)


if __name__ == "__main__":
    main()