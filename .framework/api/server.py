"""FastAPI server for the framework dashboard.

Run:
    uvicorn .framework.api.server:app --host 127.0.0.1 --port 8096 --reload

Endpoints (F0):
    GET  /framework/overview  -> aggregated snapshot
    GET  /framework/health    -> liveness + readiness
    GET  /framework/config    -> all configs (rates, thresholds, tiers, actors)
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services import config_reader, pizarra_reader, queue_reader  # noqa: E402

app = FastAPI(
    title="SMT-ONIC Framework API",
    description="Salud del equipo multi-agente (clip + ollama + Wilson Herrera) — proyecto SMT-ONIC.",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _agent_activity(actors_cfg: dict, thresholds: dict) -> list[dict]:
    hb_warn = thresholds["heartbeat"]["warn_after_minutes"] * 60
    hb_stale = thresholds["heartbeat"]["stale_after_minutes"] * 60
    last_hour = pizarra_reader.in_window(3600)
    last_24h = pizarra_reader.in_window(86400)
    all_msgs = pizarra_reader.all_messages()

    actor_ids = [actors_cfg["director"]["id"]] + [a["id"] for a in actors_cfg["agents"]]
    out = []
    now_ts = _now().timestamp()
    for aid in actor_ids:
        h = sum(1 for m in last_hour if m["actor"] == aid)
        d = sum(1 for m in last_24h if m["actor"] == aid)
        actor_msgs = [m for m in all_msgs if m["actor"] == aid and m["ts"]]
        last_ts = max((m["ts"] for m in actor_msgs), default=None)
        secs_since = None
        hb = "unknown"
        if last_ts is not None:
            ts = last_ts if last_ts.tzinfo else last_ts.replace(tzinfo=timezone.utc)
            secs_since = int(now_ts - ts.timestamp())
            if secs_since <= hb_warn:
                hb = "ok"
            elif secs_since <= hb_stale:
                hb = "warn"
            else:
                hb = "stale"
        out.append({
            "agent": aid,
            "messages_last_hour": h,
            "messages_last_24h": d,
            "last_activity_ts": last_ts.isoformat() if last_ts else None,
            "seconds_since_last": secs_since,
            "heartbeat_status": hb,
        })
    return out


@app.get("/framework/health")
def health():
    checks = {}
    try:
        config_reader.all_configs()
        checks["config"] = True
    except Exception:
        checks["config"] = False
    try:
        pizarra_reader.all_messages()
        checks["pizarra"] = True
    except Exception:
        checks["pizarra"] = False
    try:
        queue_reader.all_tasks()
        checks["queue"] = True
    except Exception:
        checks["queue"] = False

    status = "ok" if all(checks.values()) else ("degraded" if any(checks.values()) else "down")
    return {"status": status, "checks": checks, "generated_at": _now().isoformat()}


@app.get("/framework/config")
def get_config():
    return config_reader.all_configs()


@app.get("/framework/overview")
def overview():
    actors_cfg = config_reader.actors()
    thresholds = config_reader.thresholds()

    activity = _agent_activity(actors_cfg, thresholds)

    queue_status = queue_reader.status_summary()
    open_blocks = queue_reader.blocked_count()
    open_audits = sum(1 for m in pizarra_reader.by_tag("PRE-MERGE-AUDIT-REQ"))
    open_findings = sum(1 for m in pizarra_reader.by_tag("HALLAZGO"))

    return {
        "generated_at": _now().isoformat(),
        "director": actors_cfg["director"],
        "agents": actors_cfg["agents"],
        "activity": activity,
        "queue_summary": queue_status,
        "open_blocks": open_blocks,
        "open_audit_requests": open_audits,
        "open_findings": open_findings,
        "cost_today_usd": 0.0,
        "cost_month_usd": 0.0,
        "infra_ok": None,
    }


@app.get("/framework/pizarra")
def pizarra(limit: int = 100):
    msgs = pizarra_reader.recent(limit=limit)
    return {
        "count": len(msgs),
        "messages": [
            {
                "ts": m["ts"].isoformat() if m["ts"] else None,
                "actor": m["actor"],
                "tag": m["tag"],
                "para": m["para"],
                "body": m["body"],
                "task_id": m["task_id"],
            }
            for m in msgs
        ],
    }


_PROGRESS_BY_STATUS = {
    "completed": 100,
    "in_progress": 50,
    "blocked": 0,
    "pending": 0,
    "deleted": 0,
}


def _fmt_elapsed(seconds: float) -> str:
    seconds = int(max(0, seconds))
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    if seconds < 86400:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}h {m}m"
    d = seconds // 86400
    h = (seconds % 86400) // 3600
    return f"{d}d {h}h"


@app.get("/framework/queue")
def queue():
    from datetime import datetime, timezone

    tasks = queue_reader.all_tasks()
    timings = pizarra_reader.task_timings()
    now = datetime.now(timezone.utc)

    enriched = []
    for t in tasks:
        status = t.get("status") or "unknown"
        tid = t.get("id")
        tinfo = timings.get(tid) or {}
        first_ts = tinfo.get("first_ts")
        last_ts = tinfo.get("last_ts")

        elapsed_s = None
        if first_ts:
            end = last_ts if status in ("completed", "deleted") else now
            try:
                elapsed_s = (end - first_ts).total_seconds()
            except Exception:
                elapsed_s = None

        enriched.append({
            **t,
            "progress_pct": _PROGRESS_BY_STATUS.get(status, 0),
            "elapsed_s": elapsed_s,
            "elapsed_str": _fmt_elapsed(elapsed_s) if elapsed_s is not None else "—",
            "first_seen": first_ts.isoformat() if first_ts else None,
            "last_seen": last_ts.isoformat() if last_ts else None,
        })

    return {
        "count": len(tasks),
        "by_status": queue_reader.status_summary(),
        "by_owner": queue_reader.owner_summary(),
        "by_tier": queue_reader.tier_summary(),
        "by_priority": queue_reader.priority_summary(),
        "blocked": queue_reader.blocked_count(),
        "tasks": enriched,
    }
