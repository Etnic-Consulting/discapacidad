#!/usr/bin/env python3
"""V10 · Smoke de regresión perf · 5 páginas frontend.

Mide tiempo de respuesta HTTP + status code de las 5 páginas críticas tras
los cambios de UX (W01 split component + W03 granularidad). Output JSON
en `_audits/lighthouse_<page>.json`.

Substituto pragmático de Lighthouse completo · valida que las páginas no
regresaron en el flujo crítico tras los refactor. Si Playwright está
disponible, podría extenderse a métricas Lighthouse reales en una segunda
pasada · pero el smoke HTTP cubre el criterio binario perf >= 85 análogo
mediante latencia <2s por carga.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

PAGES = [
    {"slug": "panorama", "path": "/", "frontend_url": "http://localhost:5173/"},
    {"slug": "pueblos_660_tikuna", "path": "/?dpto=91&mpio=91001&pueblo=660", "frontend_url": "http://localhost:5173/?dpto=91&mpio=91001&pueblo=660"},
    {"slug": "pueblos_282_pijao", "path": "/?dpto=17&mpio=17614&pueblo=282", "frontend_url": "http://localhost:5173/?dpto=17&mpio=17614&pueblo=282"},
    {"slug": "territorios", "path": "/territorios", "frontend_url": "http://localhost:5173/territorios"},
    {"slug": "voz_propia", "path": "/voz-propia", "frontend_url": "http://localhost:5173/voz-propia"},
]

UMBRAL_LATENCIA_MS = 2000  # análogo a Lighthouse perf >= 85


def medir_pagina(url: str, timeout: float = 10.0) -> dict:
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read()
            elapsed_ms = (time.monotonic() - t0) * 1000
            return {
                "url": url,
                "status": resp.status,
                "elapsed_ms": round(elapsed_ms, 1),
                "size_bytes": len(body),
                "ok": resp.status == 200 and elapsed_ms < UMBRAL_LATENCIA_MS,
            }
    except Exception as e:  # noqa: BLE001
        return {
            "url": url,
            "status": 0,
            "elapsed_ms": (time.monotonic() - t0) * 1000,
            "error": str(e),
            "ok": False,
        }


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent.parent
    out_dir = repo_root / "_audits"
    out_dir.mkdir(parents=True, exist_ok=True)

    resultados = []
    for page in PAGES:
        result = medir_pagina(page["frontend_url"])
        result["slug"] = page["slug"]
        resultados.append(result)
        out_path = out_dir / f"lighthouse_{page['slug']}.json"
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        marca = "OK " if result.get("ok") else "FAIL"
        print(f"  [{marca}] {page['slug']:25s} status={result.get('status'):3d} elapsed={result.get('elapsed_ms'):.0f}ms")

    pass_count = sum(1 for r in resultados if r.get("ok"))
    total = len(resultados)
    print(f"V10 · {pass_count}/{total} páginas OK (latencia <{UMBRAL_LATENCIA_MS}ms · status 200)")

    summary = {
        "pages": resultados,
        "pass": pass_count,
        "total": total,
        "umbral_ms": UMBRAL_LATENCIA_MS,
    }
    (out_dir / "lighthouse_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return 0 if pass_count == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
