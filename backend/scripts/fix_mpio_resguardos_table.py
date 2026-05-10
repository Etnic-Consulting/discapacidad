#!/usr/bin/env python3
"""W17 · Fix quirúrgico tabla 'Resguardos asociados' en mpios flagged.

Los HTMLs mpio tienen la tabla con columnas Dpto/Municipio vacías (`—`).
Lee `_audits/flagged_informes.csv`, para cada mpio:
1. Lee el JSON canonical del mpio (tiene cod_dpto · nom_dpto · nom_mpio)
2. Lee `smt_geo.resguardos` para obtener mpio + dpto reales por resguardo
3. Reemplaza las celdas `—` en la tabla "Resguardos asociados" con valores reales

Idempotente · NO regenera HTML completo · solo modifica filas problemáticas.
"""

from __future__ import annotations

import csv
import os
import re
import sys
from pathlib import Path

import psycopg2

DB_CFG = {
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": int(os.environ.get("PG_PORT", "5450")),
    "user": os.environ.get("PG_USER", "smt_admin"),
    "password": os.environ.get("PG_PASSWORD", "smt_onic_2026"),
    "dbname": os.environ.get("PG_DB", "smt_onic"),
}


def _resguardos_lookup() -> dict[str, dict]:
    """Mapping {nombre_resguardo_upper: {nom_dpto, nom_mpio}}."""
    conn = psycopg2.connect(**DB_CFG)
    out = {}
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    UPPER(TRIM(rg.territorio)),
                    UPPER(TRIM(COALESCE(rg.dpto_cnmbr, ''))),
                    UPPER(TRIM(COALESCE(rg.mpio_cnmbr, '')))
                FROM smt_geo.resguardos rg
                WHERE rg.territorio IS NOT NULL
                """
            )
            for nombre, dpto, mpio in cur.fetchall():
                out[nombre] = {"nom_dpto": dpto, "nom_mpio": mpio}
    finally:
        conn.close()
    return out


_FILA_RX = re.compile(
    r'<tr><td>([^<]+)</td><td>—</td><td>—</td><td class="num">([^<]+)</td></tr>'
)


def _fix_html(html_path: Path, lookup: dict[str, dict]) -> int:
    try:
        text = html_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return 0

    cambios = 0

    def _repl(m: re.Match) -> str:
        nonlocal cambios
        resguardo = m.group(1).strip()
        poblacion = m.group(2)
        info = lookup.get(resguardo.upper())
        if not info:
            return m.group(0)
        dpto = info["nom_dpto"] or "—"
        mpio = info["nom_mpio"] or "—"
        cambios += 1
        return f'<tr><td>{resguardo}</td><td>{dpto}</td><td>{mpio}</td><td class="num">{poblacion}</td></tr>'

    new_text = _FILA_RX.sub(_repl, text)
    if cambios > 0:
        html_path.write_text(new_text, encoding="utf-8")
    return cambios


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent.parent
    csv_path = repo_root / "_audits" / "flagged_informes.csv"
    if not csv_path.exists():
        print(f"ERR: falta {csv_path}", file=sys.stderr)
        return 2
    informes_root = Path(__file__).resolve().parent.parent / "_static" / "informes"

    lookup = _resguardos_lookup()
    print(f"W17 · resguardos lookup: {len(lookup)} entradas")

    procesados = 0
    modificados = 0
    total_filas = 0

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["tipo"] != "mpio":
                continue
            html_path = informes_root / "mpio" / f"{row['id']}.html"
            if not html_path.exists():
                continue
            procesados += 1
            n = _fix_html(html_path, lookup)
            if n > 0:
                modificados += 1
                total_filas += n

    print(f"W17 · Procesados: {procesados} · Modificados: {modificados} · Filas arregladas: {total_filas}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
