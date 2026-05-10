#!/usr/bin/env python3
"""W15 · Reemplaza paths localhost en HTMLs de informes por paths relativos.

Idempotente · backup de cada archivo modificado en `_audits/localhost_backups/`.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

PATTERNS = [
    (re.compile(r"https?://localhost:5173/"), "/"),
    (re.compile(r"https?://localhost:8095/api/v1/"), "/api/v1/"),
    (re.compile(r"https?://localhost:8095/"), "/"),
    (re.compile(r"https?://127\.0\.0\.1:5173/"), "/"),
    (re.compile(r"https?://127\.0\.0\.1:8095/api/v1/"), "/api/v1/"),
]

OLLAMA_PATTERN = re.compile(r"https?://localhost:11434/")


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent.parent
    informes_root = Path(__file__).resolve().parent.parent / "_static" / "informes"
    backup_root = repo_root / "_audits" / "localhost_backups"
    backup_root.mkdir(parents=True, exist_ok=True)

    total = 0
    modificados = 0
    counts = {p.pattern: 0 for p, _ in PATTERNS}
    ollama_refs = 0

    for html_path in informes_root.rglob("*.html"):
        total += 1
        try:
            text = html_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        original = text

        if OLLAMA_PATTERN.search(text):
            ollama_refs += 1

        for pat, repl in PATTERNS:
            new_text, n = pat.subn(repl, text)
            if n > 0:
                counts[pat.pattern] += n
                text = new_text

        if text != original:
            backup_path = backup_root / f"{html_path.parent.name}_{html_path.name}.bak"
            if not backup_path.exists():
                shutil.copy2(html_path, backup_path)
            html_path.write_text(text, encoding="utf-8")
            modificados += 1

    print(f"W15 · Procesados: {total} · Modificados: {modificados}")
    print("       Patterns reemplazados:")
    for pat, count in counts.items():
        print(f"         · {pat} ({count})")
    print(f"       localhost:11434 (Ollama) refs detectados: {ollama_refs} (no modificados)")

    restantes_path = list(informes_root.rglob("*.html"))
    restantes = sum(
        1 for p in restantes_path
        if "localhost" in p.read_text(encoding="utf-8", errors="ignore")
    )
    print(f"       HTMLs con `localhost` post-fix: {restantes}")
    print(f"       Backups en {backup_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
