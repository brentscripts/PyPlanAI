from __future__ import annotations

import re
from pathlib import Path

from .models import Task

PRIORITY_RE = re.compile(r"!([1-5])\b")
TASK_LINE_RE = re.compile(r"^\s*-\s+(.*)$")
NOTES_LINE_RE = re.compile(r"^\s+notes:\s*(.*)$", re.IGNORECASE)

def parse_week_file(path: str | Path, source_week: str = "") -> list[Task]:
    text = Path(path).read_text(encoding="utf-8")
    tasks: list[Task] = []
    current: Task | None = None

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue

        notes_match = NOTES_LINE_RE.match(raw_line)
        if notes_match and current is not None:
            current.notes = notes_match.group(1).strip()
            continue

        task_match = TASK_LINE_RE.match(raw_line)
        if task_match:
            if current is not None:
                tasks.append(current)
            body = task_match.group(1).strip()
            priority = 3
            pr_match = PRIORITY_RE.search(body)
            if pr_match:
                priority = int(pr_match.group(1))
                body = PRIORITY_RE.sub("", body).strip()
            current = Task(id=None, title=body, priority=priority, source_week=source_week)

    if current is not None:
                tasks.append(current)
    return tasks