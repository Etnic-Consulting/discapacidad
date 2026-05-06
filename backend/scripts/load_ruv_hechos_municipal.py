"""
load_ruv_hechos_municipal.py
Carga CSV ruv_hechos_municipal_indigena.csv -> ext.ruv_hechos_municipal
K02 · Sprint S3_completitud · SMT-ONIC
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
CSV_PATH = r"C:\Users\wilso\Desktop\discapacidad\fuentes_externas\RUV\ruv_hechos_municipal_indigena.csv"
CHUNK_SIZE = 5000

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5450)),
    "dbname": os.getenv("DB_NAME", "smt_onic"),
    "user": os.getenv("DB_USER", "smt_admin"),
    "password": os.getenv("DB_PASSWORD", "smt_onic_2026"),
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def pad_dpto(val) -> str | None:
    """Pad departamento a 2 chars: '5' -> '05', '11' -> '11'."""
    if pd.isna(val) or str(val).strip() == "":
        return None
    s = str(int(float(str(val).strip())))
    return s.zfill(2)


def pad_mpio(val) -> str | None:
    """Pad municipio a 5 chars: '5001' -> '05001'."""
    if pd.isna(val) or str(val).strip() == "":
        return None
    s = str(int(float(str(val).strip())))
    return s.zfill(5)


def safe_int(val) -> int | None:
    """Cast a int, devuelve None si vacío o no parseable."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s == "":
        return None
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def parse_fecha(val) -> str | None:
    """Parse fecha_corte 'DD/MM/YYYY HH:MM' -> 'YYYY-MM-DD'."""
    if pd.isna(val) or str(val).strip() == "":
        return None
    s = str(val).strip()
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"[K02] Leyendo CSV: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH, encoding="utf-8", dtype=str, keep_default_na=False)
    print(f"[K02] Filas CSV brutas: {len(df):,}  |  Columnas: {list(df.columns)}")

    # Mapeo columnas CSV -> BD
    # Columnas BD: fecha_corte, cod_dpto, estado_depto, cod_mpio, ciudad_municipio,
    #              hecho, etnia, sexo, discapacidad, ciclo_vital,
    #              per_ocu, per_sa, eventos
    # Columnas CSV descartadas: nom_rpt, cod_pais, pais, param_hecho, per_decla, per_ubic

    # Construir rows directamente desde el DataFrame raw sin usar columnas derivadas
    # (evita que pandas convierta None -> NaN en columnas float64 al hacer iterrows)
    raw_fecha    = df["fecha_corte"].tolist()
    raw_dpto     = df["cod_estado_depto"].tolist()
    raw_depto    = df["estado_depto"].tolist()
    raw_mpio     = df["cod_ciudad_muni"].tolist()
    raw_ciudad   = df["ciudad_municipio"].tolist()
    raw_hecho    = df["hecho"].tolist()
    raw_etnia    = df["etnia"].tolist()
    raw_sexo     = df["sexo"].tolist()
    raw_disc     = df["discapacidad"].tolist()
    raw_ciclo    = df["ciclo_vital"].tolist()
    raw_ocu      = df["per_ocu"].tolist()
    raw_sa       = df["per_sa"].tolist()
    raw_eventos  = df["eventos"].tolist()

    def clean_str(v: str) -> str | None:
        s = v.strip()
        return s if s else None

    rows = []
    for i in range(len(df)):
        rows.append((
            parse_fecha(raw_fecha[i]),
            pad_dpto(raw_dpto[i]),
            clean_str(raw_depto[i]),
            pad_mpio(raw_mpio[i]),
            clean_str(raw_ciudad[i]),
            clean_str(raw_hecho[i]),
            clean_str(raw_etnia[i]),
            clean_str(raw_sexo[i]),
            clean_str(raw_disc[i]),
            clean_str(raw_ciclo[i]),
            safe_int(raw_ocu[i]),
            safe_int(raw_sa[i]),
            safe_int(raw_eventos[i]),
        ))

    print(f"[K02] Filas preparadas para insertar: {len(rows):,}")

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()
    try:
        # Count pre-carga
        cur.execute("SELECT COUNT(*) FROM ext.ruv_hechos_municipal")
        pre = cur.fetchone()[0]
        print(f"[K02] Filas BD antes (pre-carga): {pre:,}")

        # TRUNCATE + commit propio
        cur.execute("TRUNCATE TABLE ext.ruv_hechos_municipal RESTART IDENTITY")
        conn.commit()
        print("[K02] TRUNCATE completado")

        # Bulk INSERT en chunks — cada chunk con commit independiente
        insert_sql = """
            INSERT INTO ext.ruv_hechos_municipal
                (fecha_corte, cod_dpto, estado_depto, cod_mpio, ciudad_municipio,
                 hecho, etnia, sexo, discapacidad, ciclo_vital,
                 per_ocu, per_sa, eventos)
            VALUES %s
        """
        inserted = 0
        for i in range(0, len(rows), CHUNK_SIZE):
            chunk = rows[i : i + CHUNK_SIZE]
            execute_values(cur, insert_sql, chunk)
            conn.commit()
            inserted += len(chunk)
            print(f"[K02]   chunk {i//CHUNK_SIZE + 1}: {inserted:,} filas insertadas")

        # Count post-carga
        cur.execute("SELECT COUNT(*) FROM ext.ruv_hechos_municipal")
        post = cur.fetchone()[0]
        print(f"[K02] Filas BD despues (post-carga): {post:,}")

        # Etnia check
        cur.execute(
            "SELECT etnia, COUNT(*) FROM ext.ruv_hechos_municipal GROUP BY etnia ORDER BY etnia"
        )
        print("[K02] Etnias en tabla:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]:,}")

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

    print("[K02] Carga completada exitosamente.")


if __name__ == "__main__":
    main()
