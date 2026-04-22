"""Config reader with TTL cache. Files live in .framework/config/*.json."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
DEFAULT_TTL = 5.0

_cache: dict[str, tuple[float, Any]] = {}


def _load(name: str, ttl: float = DEFAULT_TTL) -> dict[str, Any]:
    now = time.monotonic()
    cached = _cache.get(name)
    if cached and (now - cached[0]) < ttl:
        return cached[1]
    path = CONFIG_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Config missing: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    _cache[name] = (now, data)
    return data


def rates() -> dict[str, Any]:
    return _load("rates")


def thresholds() -> dict[str, Any]:
    return _load("thresholds")


def tiers() -> dict[str, Any]:
    return _load("tiers")


def actors() -> dict[str, Any]:
    return _load("actors")


def all_configs() -> dict[str, Any]:
    return {
        "rates": rates(),
        "thresholds": thresholds(),
        "tiers": tiers(),
        "actors": actors(),
    }


def invalidate() -> None:
    _cache.clear()
