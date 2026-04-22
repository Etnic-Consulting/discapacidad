"""Pizarra reader. Parses .framework/comms/log.jsonl (append-only JSONL).

Tolerates two coexisting formats:
  A) {ts, actor, type, task, summary, artifacts}
  B) {id, de, para, fecha, hora, ts, mensaje, meta:{tag, task_id, model, ...}}
Normalizes to PizarraMessage shape.
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

PIZARRA_PATH = Path(__file__).resolve().parents[3] / ".framework" / "comms" / "log.jsonl"
TTL_SECONDS = 5.0
_cache: dict[str, Any] = {"ts": 0.0, "rows": []}

_TAG_RE = re.compile(r"^\[([A-Z][A-Z0-9_-]+)\]")


def _parse_ts(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        s = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
    ts = _parse_ts(raw.get("ts"))
    if "mensaje" in raw:
        meta = raw.get("meta") or {}
        msg = raw.get("mensaje", "")
        tag = meta.get("tag")
        if not tag:
            m = _TAG_RE.match(msg.strip())
            tag = m.group(1) if m else "OTHER"
        return {
            "ts": ts,
            "actor": raw.get("de") or "unknown",
            "tag": tag,
            "para": raw.get("para"),
            "body": msg,
            "task_id": meta.get("task_id"),
            "raw": raw,
        }
    return {
        "ts": ts,
        "actor": raw.get("actor") or "unknown",
        "tag": raw.get("type") or "OTHER",
        "para": raw.get("para"),
        "body": raw.get("summary") or raw.get("body"),
        "task_id": raw.get("task") or raw.get("task_id"),
        "raw": raw,
    }


def _read_all() -> list[dict[str, Any]]:
    now = time.monotonic()
    if (now - _cache["ts"]) < TTL_SECONDS and _cache["rows"]:
        return _cache["rows"]
    rows: list[dict[str, Any]] = []
    if PIZARRA_PATH.exists():
        with PIZARRA_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(_normalize(json.loads(line)))
                except json.JSONDecodeError:
                    continue
    _cache["ts"] = now
    _cache["rows"] = rows
    return rows


def all_messages() -> list[dict[str, Any]]:
    return list(_read_all())


def recent(limit: int = 100) -> list[dict[str, Any]]:
    rows = _read_all()
    rows_sorted = sorted(
        rows, key=lambda r: r["ts"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True
    )
    return rows_sorted[:limit]


def by_tag(tag: str) -> list[dict[str, Any]]:
    return [r for r in _read_all() if r["tag"] == tag]


def by_actor(actor: str) -> list[dict[str, Any]]:
    return [r for r in _read_all() if r["actor"] == actor]


def in_window(seconds: int) -> list[dict[str, Any]]:
    cutoff = datetime.now(timezone.utc).timestamp() - seconds
    out: list[dict[str, Any]] = []
    for r in _read_all():
        ts = r["ts"]
        if ts is None:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts.timestamp() >= cutoff:
            out.append(r)
    return out


_START_TAGS = {"EMPEZANDO", "SESSION-START", "ROUTING-DECISION", "TASK-CREATED"}
_END_TAGS = {"ENTREGADO", "APROBADO", "VERIFICADO"}


def task_timings() -> dict[str, dict[str, Any]]:
    """Para cada task_id, retorna {first_ts, last_ts, last_tag} derivado de pizarra."""
    out: dict[str, dict[str, Any]] = {}
    for r in _read_all():
        tid = r.get("task_id")
        if not tid:
            continue
        ts = r.get("ts")
        if ts is None:
            continue
        entry = out.setdefault(tid, {"first_ts": ts, "last_ts": ts, "last_tag": r.get("tag")})
        if ts < entry["first_ts"]:
            entry["first_ts"] = ts
        if ts >= entry["last_ts"]:
            entry["last_ts"] = ts
            entry["last_tag"] = r.get("tag")
    return out


def append(entry: dict[str, Any]) -> None:
    """Append a raw entry to the pizarra. Caller controls schema (use format B)."""
    PIZARRA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PIZARRA_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    _cache["ts"] = 0.0
