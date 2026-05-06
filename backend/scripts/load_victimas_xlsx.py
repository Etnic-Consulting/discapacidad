"""
Adapter del loader load_victimas.py para leer LB_UNIV_VICT_INDIGENA.xlsx
en lugar del UNIVERSO crudo TXT (que no existe en disco).

Fuente: LB_UNIV_VICT_INDIGENA.xlsx (128 MB · 787K filas · 35 cols)
Schema confirmado por VARIABLES UNIVERSO VICTIMAS LB.xlsx (diccionario UARIV).

Ejecución:
    python scripts/load_victimas_xlsx.py
    python scripts/load_victimas_xlsx.py --file <ruta.xlsx> --chunk-size 200000

---
NOTA B2 · Mapping IDPERSONA → CONSPERSONA
---------------------------------------------------------------------------
El TXT crudo UARIV (universo Colombia entero) usa columna IDPERSONA como
identificador único de persona. El XLSX línea base indígena (LB_UNIV_VICT_INDIGENA)
usa CONSPERSONA como campo equivalente según el diccionario oficial
"VARIABLES UNIVERSO VICTIMAS LB.xlsx" (UARIV).

Por tanto, victimas.universo.idpersona almacena el valor de CONSPERSONA.
Cualquier JOIN futuro entre este loader y el UNIVERSO completo TXT debe usar
este campo con precaución: CONSPERSONA ≠ IDPERSONA en todos los casos;
son campos equivalentes en función pero no necesariamente coincidentes
en su espacio de valores. El diccionario UARIV es la fuente autoritativa.
---------------------------------------------------------------------------
"""

import argparse
import os
import sys
import time
import unicodedata
from datetime import datetime, date
from pathlib import Path

import openpyxl
import psycopg2
from psycopg2.extras import execute_values

DATABASE_URL_SYNC = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://smt_admin:smt_onic_2026@localhost:5450/smt_onic",
)

DEFAULT_FILE = Path(os.getenv(
    "VICTIMAS_XLSX",
    r"C:\Users\wilso\Desktop\discapacidad\Bases Uariv-20260506T040813Z-3-001\Bases Uariv\LB-Victimas -Unica\LB_UNIV_VICT_INDIGENA.xlsx",
))

CHUNK_SIZE = 200_000
SHEET_NAME = "LB_UNIV_VICT_INDIGENA"

EXPECTED_HEADER = [
    "CONSPERSONA", "ORIGEN", "FUENTE", "PROGRAMA", "IDHOGAR",
    "FECHANACIMIENTO", "PERTENENCIAETNICA", "GENERO", "PARAM_HECHO", "HECHO",
    "FECHAOCURRENCIA", "CODDANEMUNICIPIOOCURRENCIA", "DEPARTAMENTO_OCU",
    "MUNICIPIO_OCU", "PRESUNTOACTOR", "PRESUNTOVICTIMIZANTE", "TIPOPOBLACION",
    "TIPOVICTIMA", "PAIS", "CIUDAD", "FECHAVALORACION", "ESTADOVICTIMA",
    "IDSINIESTRO", "IDMIJEFE", "TIPODESPLAZAMIENTO", "RELACION",
    "CODDANELLEGADA", "DISCAPACIDAD", "DESCRIPCIONDISCAPACIDAD", "FUD_FICHA",
]

# Columnas mínimas críticas que DEBEN existir en el XLSX; si falta alguna → ValueError (B3)
REQUIRED_COLUMNS = [
    "CONSPERSONA", "PERTENENCIAETNICA", "HECHO", "FECHAOCURRENCIA",
    "CODDANEMUNICIPIOOCURRENCIA", "DISCAPACIDAD", "DESCRIPCIONDISCAPACIDAD",
]


def clean_tipo_discapacidad(desc: str | None) -> str:
    """Clasifica DESCRIPCIONDISCAPACIDAD en categorias canonicas."""
    if not desc:
        return "SIN_INFORMACION"
    d = str(desc).upper().strip()
    if d in ("", "NA", "NULL", "0", "NO APLICA", "NINGUNA", "#NAME?"):
        return "SIN_INFORMACION"

    # M1 · Criterio MULTIPLE deliberadamente más permisivo que el loader original:
    # clasifica como MULTIPLE si hay ≥2 indicadores de tipo distinto O si el
    # string contiene la palabra "MULTIPLE" explícitamente. Esto captura el
    # formato real observado en datos: 'MULTIPLE (-Física-Intelectual)'.
    indicators = 0
    for kw in ["FISIC", "VISUAL", "AUDIT", "INTELECT", "MENTAL", "PSICO",
               "COGNI", "MOTRI", "MOTOR", "MOVIL", "CEGUERA", "SORDER",
               "SORDO", "CIEGO"]:
        if kw in d:
            indicators += 1
    if indicators >= 2 or "MULTIPLE" in d:
        return "MULTIPLE"

    if any(k in d for k in ["FISIC", "MOTRI", "MOTOR", "MOVIL", "EXTREMID",
                             "PARALISIS", "AMPUTAC", "PARAPLE", "CUADRIPLE",
                             "HEMIPLE", "CAMINAR", "DESPLAZAR", "LLEVAR",
                             "MANTENER LAS POSICIONES", "RESPIRAT", "CORAZON"]):
        return "FISICA"
    if any(k in d for k in ["VISUAL", "CEGUERA", "CIEGO", "BAJA VISION",
                             "VISION", "LUZ", "OBJETOS O PERSONAS"]):
        return "VISUAL"
    if any(k in d for k in ["AUDIT", "SORDER", "SORDO", "HIPOACUSIA", "OIR"]):
        return "AUDITIVA"
    if any(k in d for k in ["INTELECT", "COGNI", "DOWN", "RETARDO", "APRENDIZ",
                             "PENSAR", "MEMORIZAR"]):
        return "INTELECTUAL"
    if any(k in d for k in ["MENTAL", "PSICO", "PSIQUI", "ESQUIZO", "BIPOLAR",
                             "RELACION", "ENTORNO"]):
        return "PSICOSOCIAL"
    return "SIN_INFORMACION"


def to_date(value) -> str | None:
    """Convierte celda Excel a fecha ISO o None.

    M2 · Fechas fantasma Excel: celdas de tipo fecha vacías se serializan como
    1899-12-30 o 1900-01-01 por el motor de openpyxl. No son fechas reales;
    se retornan como None para no contaminar la BD.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        d = value.date()
    elif isinstance(value, date):
        d = value
    else:
        s = str(value).strip()
        if not s or s.lower() in ("nan", "null", "na"):
            return None
        d = None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                d = datetime.strptime(s[:10], fmt).date()
                break
            except (ValueError, IndexError):
                continue
        if d is None:
            return None
    # M2 · filtrar fechas fantasma de Excel (celdas vacías de tipo fecha)
    if d in (date(1899, 12, 30), date(1900, 1, 1)):
        return None
    return d.isoformat()


def pad_divipola(value, length: int) -> str | None:
    """Normaliza codigo DIVIPOLA con zero-padding."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if value != value:  # NaN
            return None
        v = str(int(value))
    else:
        v = str(value).strip()
    if v in ("", "0", "nan", "null"):
        return None
    if "." in v:
        v = v.split(".")[0]
    return v.zfill(length)


def _strip_accents(s: str) -> str:
    """Elimina diacríticos (tildes) para normalización defensiva."""
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def normalize_etnia(value) -> str:
    """Normaliza pertenencia etnica a forma canonica usada en queries.

    B1 · Defensivo para variantes futuras: si el string contiene "INDIGENA"
    (incluyendo variantes con tilde como 'Indígena') pero no matchea
    exactamente ninguna forma canónica conocida (ej. 'INDIGENA-DESPLAZADO',
    'Indígena (otro)'), se normaliza a 'INDIGENA' como catch-all.
    Esto garantiza que la BD nunca tenga valores raros.
    """
    if value is None:
        return ""
    s = str(value).strip().upper()
    # Normalizar tildes para el catch-all B1
    s_ascii = _strip_accents(s)
    if "INDIGENA (ACREDITADO" in s_ascii or "ACREDITADO RA" in s_ascii:
        return "INDIGENA ACREDITADO RA"
    if s_ascii == "INDIGENA":
        return "INDIGENA"
    # B1 · catch-all: cualquier string que contenga "INDIGENA" → canónico
    if "INDIGENA" in s_ascii:
        return "INDIGENA"
    return s[:60]


def load_pueblo_lookup(conn) -> dict:
    """cod_mpio -> (pueblo_dominante, cod_pueblo, confianza)."""
    cur = conn.cursor()
    cur.execute("""
        SELECT pdm.cod_mpio, pdm.pueblo_dominante, pdm.confianza,
               pi.cod_pueblo
        FROM pueblo.pueblo_dominante_mpio pdm
        LEFT JOIN cat.pueblos_indigenas pi
            ON UPPER(pdm.pueblo_dominante) = UPPER(pi.nombre)
        WHERE pdm.periodo = '2018'
    """)
    lookup = {}
    for cod_mpio, pueblo, confianza, cod_pueblo in cur.fetchall():
        lookup[cod_mpio] = (pueblo, cod_pueblo, confianza)
    print(f"  Pueblo lookup: {len(lookup)} municipios")
    return lookup


def setup_tables(conn):
    cur = conn.cursor()
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
    cur.execute("TRUNCATE TABLE victimas.universo CASCADE")
    cur.execute("TRUNCATE TABLE victimas.resumen_pueblo_hecho CASCADE")
    conn.commit()
    print("  Tables ready · TRUNCATEd")


def insert_chunk(cur, data):
    execute_values(cur, """
        INSERT INTO victimas.universo
            (idpersona, idhogar, pertenencia_etnica, genero, fecha_nacimiento,
             hecho, fecha_ocurrencia, cod_mpio_ocurrencia, cod_mpio_residencia,
             zona_ocurrencia, presunto_actor, tipo_victima, estado_victima,
             discapacidad, descripcion_discapacidad, tipo_discapacidad_limpia,
             cod_pueblo_imputado, pueblo_imputado, confianza_imputacion)
        VALUES %s
    """, data, page_size=10000)


def load_xlsx(conn, filepath: Path, chunk_size: int = CHUNK_SIZE):
    if not filepath.exists():
        print(f"  ERROR: file not found: {filepath}")
        return

    setup_tables(conn)
    pueblo_lookup = load_pueblo_lookup(conn)

    print(f"  Reading: {filepath}")
    print(f"  Sheet: {SHEET_NAME} · Chunk: {chunk_size:,}")
    cur = conn.cursor()

    # M5 · Envolver workbook en try/finally para garantizar wb.close()
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    try:
        ws = wb[SHEET_NAME]
        rows_iter = ws.iter_rows(values_only=True)

        header = next(rows_iter)
        header = [str(h).strip() if h is not None else "" for h in header]
        col_idx = {name: i for i, name in enumerate(header)}
        print(f"  Header: {len(header)} cols")

        # B3 · Validar columnas críticas antes de procesar
        missing = [c for c in REQUIRED_COLUMNS if c not in col_idx]
        if missing:
            raise ValueError(
                f"XLSX header falta columnas criticas: {missing}. "
                f"Columnas encontradas: {list(col_idx.keys())}"
            )

        def col(row, name):
            i = col_idx.get(name)
            return row[i] if i is not None and i < len(row) else None

        chunk = []
        total = 0
        t0 = time.time()

        for raw in rows_iter:
            if all(v is None for v in raw):
                continue
            consp = col(raw, "CONSPERSONA")
            idpersona = str(int(consp))[:20] if isinstance(consp, (int, float)) else (str(consp).strip()[:20] if consp else None)
            idhogar = col(raw, "IDHOGAR")
            idhogar = str(int(idhogar))[:20] if isinstance(idhogar, (int, float)) else (str(idhogar).strip()[:20] if idhogar else None)
            pertenencia = normalize_etnia(col(raw, "PERTENENCIAETNICA"))
            genero = (str(col(raw, "GENERO")).strip()[:20]) if col(raw, "GENERO") else None
            fecha_nac = to_date(col(raw, "FECHANACIMIENTO"))
            hecho = (str(col(raw, "HECHO")).strip()[:200]) if col(raw, "HECHO") else None
            fecha_ocu = to_date(col(raw, "FECHAOCURRENCIA"))
            cod_mpio_ocu = pad_divipola(col(raw, "CODDANEMUNICIPIOOCURRENCIA"), 5)
            cod_mpio_res = pad_divipola(col(raw, "CODDANELLEGADA"), 5)
            zona = None  # no existe en LB indigena · NULL
            actor = (str(col(raw, "PRESUNTOACTOR")).strip()[:100]) if col(raw, "PRESUNTOACTOR") else None
            tipo_vic = (str(col(raw, "TIPOVICTIMA")).strip()[:20]) if col(raw, "TIPOVICTIMA") else None
            estado_vic = (str(col(raw, "ESTADOVICTIMA")).strip()[:30]) if col(raw, "ESTADOVICTIMA") else None
            disc_raw = col(raw, "DISCAPACIDAD")
            if isinstance(disc_raw, (int, float)):
                disc = "1" if int(disc_raw) == 1 else "0"
            else:
                disc = "1" if str(disc_raw).strip() in ("1", "SI", "Si") else "0"
            desc_disc = col(raw, "DESCRIPCIONDISCAPACIDAD")
            desc_disc_str = str(desc_disc).strip() if desc_disc else None

            tipo_disc = clean_tipo_discapacidad(desc_disc_str) if disc == "1" else None

            info = pueblo_lookup.get(cod_mpio_ocu)
            cod_pueblo_imp, pueblo_imp, confianza_imp = (None, None, None)
            if info:
                pueblo_imp, cod_pueblo_imp, confianza_imp = info

            # M3 · Cast confianza_imputacion a string (columna destino VARCHAR(10))
            if confianza_imp is not None:
                if isinstance(confianza_imp, float):
                    confianza_imp = f"{confianza_imp:.4f}"[:10]
                else:
                    confianza_imp = str(confianza_imp)[:10]

            chunk.append((
                idpersona, idhogar, pertenencia, genero, fecha_nac,
                hecho, fecha_ocu, cod_mpio_ocu, cod_mpio_res,
                zona, actor, tipo_vic, estado_vic,
                disc, (desc_disc_str[:500] if desc_disc_str else None), tipo_disc,
                cod_pueblo_imp, pueblo_imp, confianza_imp,
            ))

            if len(chunk) >= chunk_size:
                insert_chunk(cur, chunk)
                total += len(chunk)
                elapsed = time.time() - t0
                rate = total / elapsed if elapsed > 0 else 0
                print(f"    {total:>12,} rows ({rate:,.0f}/s)")
                conn.commit()
                chunk = []

        if chunk:
            insert_chunk(cur, chunk)
            total += len(chunk)
            conn.commit()

        print(f"  Loaded: {total:,} rows in {time.time()-t0:.1f}s")

        # Resumen por pueblo+hecho (solo indigenas con disc + pueblo imputado)
        print("  Building victimas.resumen_pueblo_hecho...")
        cur.execute("""
            INSERT INTO victimas.resumen_pueblo_hecho
                (cod_pueblo_imputado, pueblo_imputado, hecho, tipo_disc_limpia, cod_dpto, cod_mpio, cantidad)
            SELECT cod_pueblo_imputado, pueblo_imputado, hecho,
                   tipo_discapacidad_limpia,
                   LEFT(cod_mpio_ocurrencia, 2), cod_mpio_ocurrencia,
                   COUNT(*) AS cantidad
            FROM victimas.universo
            WHERE pertenencia_etnica IN ('INDIGENA', 'INDIGENA ACREDITADO RA')
              AND discapacidad = '1'
              AND cod_pueblo_imputado IS NOT NULL
            GROUP BY cod_pueblo_imputado, pueblo_imputado, hecho,
                     tipo_discapacidad_limpia, LEFT(cod_mpio_ocurrencia, 2), cod_mpio_ocurrencia
        """)
        conn.commit()

        cur.execute("SELECT COUNT(*) FROM victimas.resumen_pueblo_hecho")
        print(f"  resumen_pueblo_hecho: {cur.fetchone()[0]:,} rows")
        cur.execute("""
            SELECT COUNT(*) FROM victimas.universo
            WHERE pertenencia_etnica IN ('INDIGENA', 'INDIGENA ACREDITADO RA')
              AND discapacidad = '1'
        """)
        print(f"  Indigenas con discapacidad cargados: {cur.fetchone()[0]:,}")
        cur.execute("""
            SELECT COUNT(*) FROM victimas.universo
            WHERE pertenencia_etnica IN ('INDIGENA', 'INDIGENA ACREDITADO RA')
              AND discapacidad = '1'
              AND pueblo_imputado IS NOT NULL
        """)
        print(f"  Indigenas con disc Y pueblo imputado: {cur.fetchone()[0]:,}")

    finally:
        # M5 · Garantizar cierre del workbook para liberar file handle
        wb.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE)
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    args = parser.parse_args()

    conn = psycopg2.connect(DATABASE_URL_SYNC)
    print(f"Connected: {DATABASE_URL_SYNC.split('@')[1]}")
    t0 = time.time()
    load_xlsx(conn, args.file, args.chunk_size)
    print(f"Total: {time.time()-t0:.1f}s")
    conn.close()


if __name__ == "__main__":
    main()
