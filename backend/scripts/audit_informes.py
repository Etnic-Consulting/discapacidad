#!/usr/bin/env python3
"""W08 · Auditor de informes pre-renderizados con 5 heuristicas binarias.

Recorre `backend/_static/informes/<tipo>/<id>.json` y flagea los incompletos.
Output: `_audits/flagged_informes.csv` con cols `tipo,id,size_kb,truncado,
falta_seccion,llm_bloqueado,sin_citas,todos_cero`.

Heuristicas:
  H1 truncado: size < umbral por tipo (macro 8KB, dpto 5KB, mpio 2KB,
              pueblo 2KB, resguardo 1.5KB)
  H2 falta_seccion: no contiene una de {info_basica, territorial, conflicto, icv}
  H3 llm_bloqueado: contiene `[VERIFICAR]`, `BLOQUEADO`, `lo siento`, `sin
                    informacion`, `TODO`
  H4 sin_citas: no contiene `DANE` ni `CNPV` en cuerpo
  H5 todos_cero: todos los `value` numericos son 0
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

UMBRAL_TRUNCADO = {
    "macro": 8000,
    "dpto": 5000,
    "mpio": 2000,
    "pueblo": 2000,
    "resguardo": 1500,
}
SECCIONES_OBLIGATORIAS = {"capacidades_diversas", "territorial", "conflicto", "icv"}
LLM_BLOQUEADO_PATRONES = (
    "[VERIFICAR]",
    "BLOQUEADO",
    "lo siento",
    "Sin informacion",
    "Sin información",
    "TODO",
    "<placeholder>",
)
CITAS_REQUERIDAS = ("DANE", "CNPV")


def heuristicas(path: Path, tipo: str) -> dict:
    flags = {
        "tipo": tipo,
        "id": path.stem,
        "size_kb": 0.0,
        "truncado": 0,
        "falta_seccion": 0,
        "llm_bloqueado": 0,
        "sin_citas": 0,
        "todos_cero": 0,
    }
    try:
        size = path.stat().st_size
        flags["size_kb"] = round(size / 1024, 1)
        flags["truncado"] = int(size < UMBRAL_TRUNCADO.get(tipo, 1500))
        text = path.read_text(encoding="utf-8", errors="ignore")
        data = json.loads(text)
    except (OSError, json.JSONDecodeError):
        flags["truncado"] = 1
        return flags

    secciones = data.get("secciones", {})
    if isinstance(secciones, dict):
        flags["falta_seccion"] = int(bool(SECCIONES_OBLIGATORIAS - set(secciones.keys())))

    # llm_bloqueado: SOLO buscar en .llm.json (texto LLM puro · evita falsos positivos
    # por valores de datos como "Sin informacion" que son legítimos en el canonical)
    llm_path = Path(str(path).replace(".json", ".llm.json"))
    text_llm = ""
    if llm_path.exists():
        try:
            text_llm = llm_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            pass

    flags["llm_bloqueado"] = int(bool(text_llm) and any(p in text_llm for p in LLM_BLOQUEADO_PATRONES))
    # sin_citas: canonical con _meta (SQL trazable) ó citas en LLM enriquecido
    has_meta = '"_meta"' in text or '"query"' in text
    has_citas_texto = any(c in text_llm for c in CITAS_REQUERIDAS) or any(c in text for c in CITAS_REQUERIDAS)
    flags["sin_citas"] = int(not (has_meta or has_citas_texto))

    valores: list[float] = []

    def _walk(obj):
        if isinstance(obj, dict):
            v = obj.get("value")
            if isinstance(v, (int, float)):
                valores.append(float(v))
            for sub in obj.values():
                _walk(sub)
        elif isinstance(obj, list):
            for sub in obj:
                _walk(sub)

    _walk(data)
    flags["todos_cero"] = int(bool(valores) and all(v == 0 for v in valores))
    return flags


def is_flagged(flags: dict) -> bool:
    return any(int(flags[k]) for k in ("truncado", "falta_seccion", "llm_bloqueado", "sin_citas", "todos_cero"))


def main() -> int:
    raiz = Path(__file__).resolve().parent.parent / "_static" / "informes"
    if not raiz.exists():
        print(f"ERR: no existe {raiz}", file=sys.stderr)
        return 2

    out_dir = Path(__file__).resolve().parent.parent.parent / "_audits"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / "flagged_informes.csv"

    cols = ["tipo", "id", "size_kb", "truncado", "falta_seccion", "llm_bloqueado", "sin_citas", "todos_cero"]
    rows_flagged: list[dict] = []
    total = 0

    for tipo_dir in sorted(raiz.iterdir()):
        if not tipo_dir.is_dir():
            continue
        tipo = tipo_dir.name
        for json_path in sorted(tipo_dir.glob("*.json")):
            if json_path.name.endswith(".llm.json"):
                continue
            total += 1
            flags = heuristicas(json_path, tipo)
            if is_flagged(flags):
                rows_flagged.append(flags)

    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for r in rows_flagged:
            writer.writerow(r)

    print(f"Auditados: {total} · Flagged: {len(rows_flagged)} · CSV: {out_csv}")

    resumen = {}
    for r in rows_flagged:
        for k in ("truncado", "falta_seccion", "llm_bloqueado", "sin_citas", "todos_cero"):
            if int(r[k]):
                resumen[k] = resumen.get(k, 0) + 1
    print("Por categoria:", resumen)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
