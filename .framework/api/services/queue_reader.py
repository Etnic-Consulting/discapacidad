"""Queue reader. Parses .framework/tasks/queue.jsonl (one task per line)."""
from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path
from typing import Any, Optional

QUEUE_PATH = Path(__file__).resolve().parents[3] / ".framework" / "tasks" / "queue.jsonl"
TTL_SECONDS = 5.0
_cache: dict[str, Any] = {"ts": 0.0, "rows": []}


def _read_all() -> list[dict[str, Any]]:
    now = time.monotonic()
    if (now - _cache["ts"]) < TTL_SECONDS and _cache["rows"]:
        return _cache["rows"]
    rows: list[dict[str, Any]] = []
    if QUEUE_PATH.exists():
        with QUEUE_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    _cache["ts"] = now
    _cache["rows"] = rows
    return rows


def all_tasks() -> list[dict[str, Any]]:
    return list(_read_all())


def by_status(status: str) -> list[dict[str, Any]]:
    return [t for t in _read_all() if t.get("status") == status]


def by_owner(owner: str) -> list[dict[str, Any]]:
    return [t for t in _read_all() if t.get("owner") == owner]


def status_summary() -> dict[str, int]:
    return dict(Counter((t.get("status") or "unknown") for t in _read_all()))


def owner_summary() -> dict[str, int]:
    return dict(Counter((t.get("owner") or "unassigned") for t in _read_all()))


def tier_summary() -> dict[str, int]:
    return dict(Counter((str(t.get("model_tier")) or "unknown") for t in _read_all()))


def priority_summary() -> dict[str, dict[str, Any]]:
    """Cuenta tareas por priority (P0/P1/...) y status. {prio: {total, by_status}}."""
    summary: dict[str, dict[str, Any]] = {}
    for t in _read_all():
        prio = t.get("priority") or "P?"
        status = t.get("status") or "unknown"
        bucket = summary.setdefault(prio, {"total": 0, "by_status": {}})
        bucket["total"] += 1
        bucket["by_status"][status] = bucket["by_status"].get(status, 0) + 1
    return summary


def blocked_count() -> int:
    open_ids = {t["id"] for t in _read_all() if t.get("status") in ("pending", "in_progress")}
    blocked = 0
    for t in _read_all():
        if t.get("status") in ("pending", "in_progress"):
            deps = t.get("depends_on") or t.get("blocked_by") or []
            if any(d in open_ids and d != t["id"] for d in deps):
                blocked += 1
    return blocked


def append(task: dict[str, Any]) -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(task, ensure_ascii=False) + "\n")
    _cache["ts"] = 0.0
