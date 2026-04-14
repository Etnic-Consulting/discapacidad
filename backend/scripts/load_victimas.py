"""
Dedicated victims data loader for SMT-ONIC.
Reads the RUV UNIVERSO file (0001_UNIVERSO_VICTIMAS_LB_ANONIMO.txt)
and loads it into victimas.universo with cleaning and pueblo imputation.

The file uses 0xBB as separator, latin-1 encoding, and has ~12M rows / 4.3GB.

Usage:
    python scripts/load_victimas.py
    python scripts/load_victimas.py --file /path/to/UNIVERSO.txt
    python scripts/load_victimas.py --chunk-size 250000
"""

import argparse
import csv
import os
import sys
import time
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATABASE_URL_SYNC = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://smt_admin:smt_onic_2026@localhost:5450/smt_onic",
)

VICTIMAS_DIR = Path(os.getenv(
    "VICTIMAS_DIR",
    r"C:\Users\wilso\Desktop\discapacidad\victimas",
))

DEFAULT_FILE = VICTIMAS_DIR / "0001_UNIVERSO_VICTIMAS_LB_ANONIMO.txt"

SEPARATOR = "\xBB"  # 0xBB = >> character used as delimiter
ENCODING = "latin-1"
CHUNK_SIZE = 500_000

# Columns we keep from the 53-column source file
# Map: source column name (uppercase) -> our column name
COLUMN_MAP = {
    "IDPERSONA": "idpersona",
    "IDHOGAR": "idhogar",
    "PERTENENCIAETNICA": "pertenencia_etnica",
    "GENERO": "genero",
    "FECHANACIMIENTO": "fecha_nacimiento",
    "HECHO": "hecho",
    "FECHAOCURRENCIADESDE": "fecha_ocurrencia",
    "CODDANEMUNICIPIOOCURRENCIA": "cod_mpio_ocurrencia",
    "CODDANEMUNIRESIDENCIA": "cod_mpio_residencia",
    "ZONAOCURRENCIA": "zona_ocurrencia",
    "PRESUNTOACTOR": "presunto_actor",
    "TIPOVICTIMA": "tipo_victima",
    "ESTADOVICTIMA": "estado_victima",
    "DISCAPACIDAD": "discapacidad",
    "DESCRIPCIONDISCAPACIDAD": "descripcion_discapacidad",
}


def clean_tipo_discapacidad(desc: str | None) -> str:
    """Classify DESCRIPCIONDISCAPACIDAD into standard categories."""
    if not desc or desc.strip() == "" or desc.strip().upper() in ("NA", "NULL", "0", "NO APLICA"):
        return "SIN_INFORMACION"

    d = desc.upper().strip()

    # Multiple disabilities
    indicators_count = 0
    for keyword in ["FISIC", "VISUAL", "AUDIT", "INTELECT", "MENTAL", "PSICO", "COGNI",
                     "MOTRI", "MOTOR", "MOVIL", "CEGUERA", "SORDER", "SORDO", "CIEGO"]:
        if keyword in d:
            indicators_count += 1
    if indicators_count >= 2:
        return "MULTIPLE"

    if any(k in d for k in ["FISIC", "MOTRI", "MOTOR", "MOVIL", "EXTREMID", "PARALISIS",
                              "AMPUTAC", "PARAPLE", "CUADRIPLE", "HEMIPLE"]):
        return "FISICA"
    if any(k in d for k in ["VISUAL", "CEGUERA", "CIEGO", "BAJA VISION", "VISION"]):
        return "VISUAL"
    if any(k in d for k in ["AUDIT", "SORDER", "SORDO", "HIPOACUSIA", "OIR"]):
        return "AUDITIVA"
    if any(k in d for k in ["INTELECT", "COGNI", "DOWN", "RETARDO", "APRENDIZ"]):
        return "INTELECTUAL"
    if any(k in d for k in ["MENTAL", "PSICO", "PSIQUI", "ESQUIZO", "BIPOLAR"]):
        return "PSICOSOCIAL"

    return "SIN_INFORMACION"


def safe_date(value: str | None) -> str | None:
    """Parse date from various formats, return ISO or None."""
    if not value or value.strip() in ("", "NA", "NULL"):
        return None
    v = value.strip()
    # Try common formats
    for fmt_in, fmt_out in [
        ("%d/%m/%Y", "%Y-%m-%d"),
        ("%Y-%m-%d", "%Y-%m-%d"),
        ("%d-%m-%Y", "%Y-%m-%d"),
        ("%Y/%m/%d", "%Y-%m-%d"),
    ]:
        try:
            from datetime import datetime
            return datetime.strptime(v[:10], fmt_in).strftime(fmt_out)
        except (ValueError, IndexError):
            continue
    return None


def pad_divipola(value: str | None, length: int) -> str | None:
    """Zero-pad a DIVIPOLA code."""
    if value is None:
        return None
    v = str(value).strip()
    if v == "" or v.lower() in ("nan", "na", "null"):
        return None
    # Remove decimals from floats like "5001.0"
    if "." in v:
        v = v.split(".")[0]
    return v.zfill(length)


def load_pueblo_lookup(conn) -> dict:
    """Load pueblo_dominante_mpio as a lookup: cod_mpio -> (pueblo, cod_pueblo_approx, confianza)."""
    cur = conn.cursor()
    cur.execute("""
        SELECT pdm.cod_mpio, pdm.pueblo_dominante, pdm.confianza,
               pi.cod_pueblo
        FROM pueblo.pueblo_dominante_mpio pdm
        LEFT JOIN cat.pueblos_indigenas pi ON UPPER(pdm.pueblo_dominante) = UPPER(pi.nombre)
        WHERE pdm.periodo = '2018'
    """)
    lookup = {}
    for row in cur.fetchall():
        cod_mpio, pueblo, confianza, cod_pueblo = row
        lookup[cod_mpio] = (pueblo, cod_pueblo, confianza)
    print(f"  Pueblo lookup loaded: {len(lookup)} municipios with dominant pueblo")
    return lookup


def load_victimas_universo(conn, filepath: Path = None, chunk_size: int = CHUNK_SIZE):
    """
    Load the UNIVERSO victims file into victimas.universo.
    Filters to keep only relevant columns, cleans disability descriptions,
    and imputes pueblo based on municipality of occurrence.
    """
    if filepath is None:
        filepath = DEFAULT_FILE

    if not filepath.exists():
        print(f"  WARNING: File not found: {filepath}")
        print("  Skipping victims load. Download the file and retry with --step victimas")
        return

    cur = conn.cursor()

    # Ensure schema and tables exist
    cur.execute("CREATE SCHEMA IF NOT EXISTS victimas")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS victimas.universo (
            id SERIAL PRIMARY KEY,
            idpersona VARCHAR(20),
            idhogar VARCHAR(20),
            pertenencia_etnica VARCHAR(60),
            genero VARCHAR(20),
            fecha_nacimiento DATE,
            hecho VARCHAR(200),
            fecha_ocurrencia DATE,
            cod_mpio_ocurrencia VARCHAR(5),
            cod_mpio_residencia VARCHAR(5),
            zona_ocurrencia VARCHAR(30),
            presunto_actor VARCHAR(100),
            tipo_victima VARCHAR(20),
            estado_victima VARCHAR(30),
            discapacidad VARCHAR(5),
            descripcion_discapacidad TEXT,
            tipo_discapacidad_limpia VARCHAR(30),
            cod_pueblo_imputado VARCHAR(3),
            pueblo_imputado VARCHAR(100),
            confianza_imputacion VARCHAR(10),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    conn.commit()

    # Truncate
    cur.execute("TRUNCATE TABLE victimas.universo CASCADE")
    print(f"  TRUNCATED victimas.universo")

    # Also ensure summary table exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS victimas.resumen_pueblo_hecho (
            id SERIAL PRIMARY KEY,
            cod_pueblo_imputado VARCHAR(3),
            pueblo_imputado VARCHAR(100),
            hecho VARCHAR(200),
            tipo_disc_limpia VARCHAR(30),
            cod_dpto VARCHAR(2),
            cod_mpio VARCHAR(5),
            cantidad INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    cur.execute("TRUNCATE TABLE victimas.resumen_pueblo_hecho CASCADE")
    conn.commit()

    # Load pueblo lookup for imputation
    pueblo_lookup = load_pueblo_lookup(conn)

    print(f"  Reading: {filepath}")
    print(f"  Separator: 0xBB, Encoding: {ENCODING}, Chunk size: {chunk_size:,}")

    total_loaded = 0
    chunk_data = []
    t0 = time.time()

    # Increase CSV field size limit for large fields
    csv.field_size_limit(sys.maxsize)

    with open(filepath, "r", encoding=ENCODING, errors="replace") as f:
        reader = csv.DictReader(f, delimiter=SEPARATOR)

        # Normalize header names (strip whitespace, uppercase)
        if reader.fieldnames:
            reader.fieldnames = [fn.strip().upper() for fn in reader.fieldnames]
            print(f"  Columns found: {len(reader.fieldnames)}")

        for i, row in enumerate(reader, 1):
            # Extract relevant columns
            idpersona = (row.get("IDPERSONA") or "").strip()[:20]
            idhogar = (row.get("IDHOGAR") or "").strip()[:20]
            pertenencia = (row.get("PERTENENCIAETNICA") or "").strip()[:60]
            genero = (row.get("GENERO") or "").strip()[:20]
            fecha_nac = safe_date(row.get("FECHANACIMIENTO"))
            hecho = (row.get("HECHO") or "").strip()[:200]
            fecha_ocu = safe_date(row.get("FECHAOCURRENCIADESDE"))
            cod_mpio_ocu = pad_divipola(row.get("CODDANEMUNICIPIOOCURRENCIA"), 5)
            cod_mpio_res = pad_divipola(row.get("CODDANEMUNIRESIDENCIA"), 5)
            zona = (row.get("ZONAOCURRENCIA") or "").strip()[:30]
            actor = (row.get("PRESUNTOACTOR") or "").strip()[:100]
            tipo_vic = (row.get("TIPOVICTIMA") or "").strip()[:20]
            estado_vic = (row.get("ESTADOVICTIMA") or "").strip()[:30]
            disc = (row.get("DISCAPACIDAD") or "").strip()[:5]
            desc_disc = (row.get("DESCRIPCIONDISCAPACIDAD") or "").strip()

            # Clean disability type
            tipo_disc_limpia = clean_tipo_discapacidad(desc_disc) if disc == "1" else None

            # Impute pueblo from municipality of occurrence
            pueblo_info = pueblo_lookup.get(cod_mpio_ocu)
            pueblo_imputado = pueblo_info[0] if pueblo_info else None
            cod_pueblo_imp = pueblo_info[1] if pueblo_info else None
            confianza_imp = pueblo_info[2] if pueblo_info else None

            chunk_data.append((
                idpersona, idhogar, pertenencia, genero, fecha_nac,
                hecho, fecha_ocu, cod_mpio_ocu, cod_mpio_res,
                zona, actor, tipo_vic, estado_vic,
                disc, desc_disc[:500] if desc_disc else None, tipo_disc_limpia,
                cod_pueblo_imp, pueblo_imputado, confianza_imp,
            ))

            if len(chunk_data) >= chunk_size:
                _insert_chunk(cur, chunk_data)
                total_loaded += len(chunk_data)
                elapsed = time.time() - t0
                rate = total_loaded / elapsed if elapsed > 0 else 0
                print(f"    {total_loaded:>12,} rows loaded ({rate:,.0f} rows/s)")
                conn.commit()
                chunk_data = []

        # Insert remaining rows
        if chunk_data:
            _insert_chunk(cur, chunk_data)
            total_loaded += len(chunk_data)
            conn.commit()

    elapsed = time.time() - t0
    print(f"  Total loaded: {total_loaded:,} rows in {elapsed:.1f}s")

    # Build summary table
    print("  Building victimas.resumen_pueblo_hecho...")
    cur.execute("""
        INSERT INTO victimas.resumen_pueblo_hecho
            (cod_pueblo_imputado, pueblo_imputado, hecho, tipo_disc_limpia, cod_dpto, cod_mpio, cantidad)
        SELECT
            cod_pueblo_imputado,
            pueblo_imputado,
            hecho,
            tipo_discapacidad_limpia,
            LEFT(cod_mpio_ocurrencia, 2) AS cod_dpto,
            cod_mpio_ocurrencia,
            COUNT(*) AS cantidad
        FROM victimas.universo
        WHERE pertenencia_etnica IN ('INDIGENA', 'INDIGENA ACREDITADO RA')
          AND discapacidad = '1'
          AND cod_pueblo_imputado IS NOT NULL
        GROUP BY cod_pueblo_imputado, pueblo_imputado, hecho,
                 tipo_discapacidad_limpia, LEFT(cod_mpio_ocurrencia, 2), cod_mpio_ocurrencia
    """)
    conn.commit()

    n_summary = 0
    cur.execute("SELECT COUNT(*) FROM victimas.resumen_pueblo_hecho")
    n_summary = cur.fetchone()[0]
    print(f"  victimas.resumen_pueblo_hecho: {n_summary:,} rows")

    n_indig_disc = 0
    cur.execute("""
        SELECT COUNT(*) FROM victimas.universo
        WHERE pertenencia_etnica IN ('INDIGENA', 'INDIGENA ACREDITADO RA')
          AND discapacidad = '1'
    """)
    n_indig_disc = cur.fetchone()[0]
    print(f"  Victimas indigenas con capacidades diversas: {n_indig_disc:,}")


def _insert_chunk(cur, data: list):
    """Insert a chunk of rows into victimas.universo."""
    execute_values(cur, """
        INSERT INTO victimas.universo
            (idpersona, idhogar, pertenencia_etnica, genero, fecha_nacimiento,
             hecho, fecha_ocurrencia, cod_mpio_ocurrencia, cod_mpio_residencia,
             zona_ocurrencia, presunto_actor, tipo_victima, estado_victima,
             discapacidad, descripcion_discapacidad, tipo_discapacidad_limpia,
             cod_pueblo_imputado, pueblo_imputado, confianza_imputacion)
        VALUES %s
    """, data, page_size=10000)


# ---------------------------------------------------------------------------
# Main (standalone execution)
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="SMT-ONIC victims data loader")
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_FILE,
        help="Path to UNIVERSO victims file",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=CHUNK_SIZE,
        help=f"Rows per insert batch (default: {CHUNK_SIZE:,})",
    )
    args = parser.parse_args()

    conn = psycopg2.connect(DATABASE_URL_SYNC)
    print(f"Connected to: {DATABASE_URL_SYNC.split('@')[1] if '@' in DATABASE_URL_SYNC else DATABASE_URL_SYNC}")

    t0 = time.time()
    load_victimas_universo(conn, filepath=args.file, chunk_size=args.chunk_size)
    elapsed = time.time() - t0

    print(f"\nTotal time: {elapsed:.1f}s")
    conn.close()


if __name__ == "__main__":
    main()
