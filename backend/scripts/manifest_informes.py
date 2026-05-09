#!/usr/bin/env python3
"""W09 · Genera MANIFEST.json con SHA256 de los 2.114 informes.

Output: `backend/_static/informes/MANIFEST.json` con shape:
{
  "generado_en": "<iso>",
  "total": <n>,
  "por_tipo": {"macro": 5, "dpto": 33, "mpio": 1121, "pueblo": 125, "resguardo": 830},
  "informes": [
    {"path": "macro/1.json", "sha256": "...", "size_bytes": 12345, "modified_iso": "..."},
    ...
  ]
}
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    raiz = Path(__file__).resolve().parent.parent / "_static" / "informes"
    if not raiz.exists():
        print(f"ERR: no existe {raiz}", file=sys.stderr)
        return 2

    informes = []
    por_tipo = {}

    for tipo_dir in sorted(raiz.iterdir()):
        if not tipo_dir.is_dir():
            continue
        tipo = tipo_dir.name
        for json_path in sorted(tipo_dir.glob("*.json")):
            if json_path.name.endswith(".llm.json"):
                continue
            stat = json_path.stat()
            rel = json_path.relative_to(raiz).as_posix()
            informes.append(
                {
                    "path": rel,
                    "sha256": sha256_file(json_path),
                    "size_bytes": stat.st_size,
                    "modified_iso": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                }
            )
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

    manifest = {
        "generado_en": datetime.now(tz=timezone.utc).isoformat(),
        "total": len(informes),
        "por_tipo": por_tipo,
        "informes": informes,
    }

    out_path = raiz / "MANIFEST.json"
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"MANIFEST: {len(informes)} informes · por_tipo={por_tipo} · output={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
