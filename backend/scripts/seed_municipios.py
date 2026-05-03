"""Seed geo.municipios desde bd_consolidada/02_prevalencia_disc_x_etnia_mpio.csv.

Lee codigos DANE de municipios (cod_mpio + cod_dpto + nom_mpio) del CSV
y hace INSERT idempotente en geo.municipios. Geometrías quedan NULL —
si se necesitan polígonos, usar load_geo.py con shapefile MGN.

Run inside the api container:
    docker exec smt-onic-api python -m scripts.seed_municipios
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_URL_SYNC = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://smt_admin:smt_onic_2026@db:5432/smt_onic",
)

_DEFAULT_DATA_ROOT = os.getenv("DISCAPACIDAD_DIR", "/data/discapacidad")
BD_CONSOLIDADA = Path(os.getenv(
    "BD_CONSOLIDADA_DIR",
    f"{_DEFAULT_DATA_ROOT}/bd_consolidada",
))
SOURCE_CSV = BD_CONSOLIDADA / "02_prevalencia_disc_x_etnia_mpio.csv"


def main() -> int:
    if not SOURCE_CSV.exists():
        print(f"ERROR: no se encuentra {SOURCE_CSV}", file=sys.stderr)
        return 1

    seen: dict[str, tuple[str, str]] = {}
    with SOURCE_CSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            cod_mpio = (row.get("cod_mpio") or "").strip()
            if not cod_mpio:
                continue
            if cod_mpio not in seen:
                seen[cod_mpio] = (
                    (row.get("cod_dpto") or "").strip(),
                    (row.get("nom_mpio") or "").strip(),
                )

    engine = create_engine(DATABASE_URL_SYNC)
    inserted = 0
    skipped = 0
    with engine.begin() as conn:
        for cod_mpio, (cod_dpto, nom_mpio) in seen.items():
            res = conn.execute(
                text("""
                    INSERT INTO geo.municipios (cod_mpio, cod_dpto, nom_mpio)
                    VALUES (:cm, :cd, :nm)
                    ON CONFLICT (cod_mpio) DO NOTHING
                """),
                {"cm": cod_mpio, "cd": cod_dpto, "nm": nom_mpio},
            )
            if res.rowcount and res.rowcount > 0:
                inserted += 1
            else:
                skipped += 1

    print(f"[ok] geo.municipios · insertados={inserted} · skipped(existían)={skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
