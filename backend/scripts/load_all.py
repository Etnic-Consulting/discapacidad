"""
Master data loader for SMT-ONIC.
Loads all CSV data into PostgreSQL following the schema in sql/001_schema.sql.

Usage:
    python scripts/load_all.py                  # Run all steps
    python scripts/load_all.py --step cnpv      # Only CNPV data
    python scripts/load_all.py --step pueblo    # Only pueblo data
    python scripts/load_all.py --step ext       # Only external sources
    python scripts/load_all.py --step victimas  # Only victims data
    python scripts/load_all.py --step indicadores # Recalculate indicators
"""

import argparse
import csv
import io
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

# Data directories -- adjust these to your environment
BD_CONSOLIDADA = Path(os.getenv(
    "BD_CONSOLIDADA_DIR",
    r"C:\Users\wilso\Desktop\discapacidad\bd_consolidada",
))
FUENTES_EXTERNAS = Path(os.getenv(
    "FUENTES_EXTERNAS_DIR",
    r"C:\Users\wilso\Desktop\discapacidad\fuentes_externas",
))
VICTIMAS_DIR = Path(os.getenv(
    "VICTIMAS_DIR",
    r"C:\Users\wilso\Desktop\discapacidad\victimas",
))


def get_conn():
    """Create a new psycopg2 connection."""
    return psycopg2.connect(DATABASE_URL_SYNC)


def pad_divipola(value: str, length: int) -> str:
    """Zero-pad a DIVIPOLA code to the expected length."""
    if value is None:
        return None
    v = str(value).strip()
    if v == "" or v.lower() == "nan":
        return None
    return v.zfill(length)


def safe_int(value) -> int | None:
    """Convert value to int, returning None on failure."""
    if value is None:
        return None
    v = str(value).strip().replace(",", "").replace(".", "")
    if v == "" or v.lower() == "nan":
        return None
    try:
        return int(v)
    except ValueError:
        return None


def safe_float(value) -> float | None:
    """Convert value to float, returning None on failure."""
    if value is None:
        return None
    v = str(value).strip().replace(",", ".")
    if v == "" or v.lower() == "nan":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def read_semicolon_csv(filepath: Path) -> list[dict]:
    """Read a semicolon-separated CSV and return list of dicts."""
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        return list(reader)


def truncate_and_report(cur, table: str):
    """Truncate a table and print status."""
    cur.execute(f"TRUNCATE TABLE {table} CASCADE")
    print(f"  TRUNCATED {table}")


def count_rows(cur, table: str) -> int:
    """Count rows in a table."""
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    return cur.fetchone()[0]


def report_count(cur, table: str):
    """Print row count for a table."""
    n = count_rows(cur, table)
    print(f"  {table}: {n:,} rows")


# ---------------------------------------------------------------------------
# Step 1: CNPV data (CSVs 01-10)
# ---------------------------------------------------------------------------
def load_cnpv(conn):
    print("\n=== STEP 1: Loading CNPV data ===")
    cur = conn.cursor()

    # 01 - prevalencia_etnia_dpto
    table = "cnpv.prevalencia_etnia_dpto"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "01_prevalencia_disc_x_etnia_dpto.csv")
    data = []
    for r in rows:
        data.append((
            "2018",
            pad_divipola(r["cod_dpto"], 2),
            r["grupo_etnico"],
            safe_int(r["pob_total"]),
            safe_int(r["pob_disc"]),
            safe_int(r["pob_no_disc"]),
            safe_float(r["tasa_x_1000"]),
            safe_float(r["prevalencia_pct"]),
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, cod_dpto, grupo_etnico, pob_total, pob_disc, pob_no_disc, tasa_x_1000, prevalencia_pct)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    # 02 - prevalencia_etnia_mpio
    table = "cnpv.prevalencia_etnia_mpio"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "02_prevalencia_disc_x_etnia_mpio.csv")
    data = []
    for r in rows:
        data.append((
            "2018",
            pad_divipola(r["cod_dpto"], 2),
            pad_divipola(r["cod_mpio"], 5),
            r["grupo_etnico"],
            safe_int(r["pob_total"]),
            safe_int(r["pob_disc"]),
            safe_float(r["tasa_x_1000"]),
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, cod_dpto, cod_mpio, grupo_etnico, pob_total, pob_disc, tasa_x_1000)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    # 03 - dificultades_etnia_dpto
    table = "cnpv.dificultades_etnia_dpto"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "03_dificultades_x_etnia_dpto.csv")
    data = []
    for r in rows:
        data.append((
            "2018",
            pad_divipola(r["cod_dpto"], 2),
            r["grupo_etnico"],
            r["dificultad"],
            safe_int(r["pob_total"]),
            safe_int(r["con_dificultad"]),
            safe_float(r["tasa_x_1000"]),
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, cod_dpto, grupo_etnico, dificultad, pob_total, con_dificultad, tasa_x_1000)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    # 04 - salud_etnia_dpto
    table = "cnpv.salud_etnia_dpto"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "04_salud_x_etnia_dpto.csv")
    data = []
    for r in rows:
        data.append((
            "2018",
            pad_divipola(r["cod_dpto"], 2),
            r["grupo_etnico"],
            r["variable"],
            r["categoria"],
            safe_int(r["valor"]),
            safe_float(r["pct"]),
            safe_int(r["total_grupo"]),
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, cod_dpto, grupo_etnico, variable, categoria, valor, pct, total_grupo)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    # 05 - disc_edad_dpto (deduplicate: CSV has repeated cod_dpto=99)
    table = "cnpv.disc_edad_dpto"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "05_disc_x_edad_dpto.csv")
    seen = set()
    data = []
    for r in rows:
        key = (pad_divipola(r["cod_dpto"], 2), r["grupo_edad"], r["discapacidad"])
        if key in seen:
            continue
        seen.add(key)
        data.append((
            "2018",
            pad_divipola(r["cod_dpto"], 2),
            r["grupo_edad"],
            r["discapacidad"],
            safe_int(r["valor"]),
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, cod_dpto, grupo_edad, discapacidad, valor)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    # 06 - disc_sexo_dpto
    table = "cnpv.disc_sexo_dpto"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "06_disc_x_sexo_dpto.csv")
    data = []
    for r in rows:
        data.append((
            "2018",
            pad_divipola(r["cod_dpto"], 2),
            r["sexo"],
            r["discapacidad"],
            safe_int(r["valor"]),
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, cod_dpto, sexo, discapacidad, valor)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    # 07 - disc_indigena_mpio
    table = "cnpv.disc_indigena_mpio"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "07_disc_indigena_mpio.csv")
    data = []
    for r in rows:
        data.append((
            "2018",
            pad_divipola(r["cod_dpto"], 2),
            pad_divipola(r["cod_mpio"], 5),
            safe_int(r["pob_indigena"]),
            safe_int(r["con_disc"]),
            safe_float(r["tasa_x_1000"]),
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, cod_dpto, cod_mpio, pob_indigena, con_disc, tasa_x_1000)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    # 08 - resumen_nacional_etnico
    table = "cnpv.resumen_nacional_etnico"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "08_resumen_nacional_etnico.csv")
    data = []
    for r in rows:
        data.append((
            "2018",
            r["grupo_etnico"],
            safe_int(r["pob_total"]),
            safe_int(r["pob_disc"]),
            safe_float(r["prevalencia_pct"]),
            safe_float(r["tasa_x_1000"]),
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, grupo_etnico, pob_total, pob_disc, prevalencia_pct, tasa_x_1000)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    # 09 - causa_disc_etnia_dpto
    table = "cnpv.causa_disc_etnia_dpto"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "09_causa_disc_x_etnia_dpto.csv")
    data = []
    for r in rows:
        data.append((
            "2018",
            pad_divipola(r["cod_dpto"], 2),
            r["grupo_etnico"],
            r["causa"],
            safe_int(r["valor"]),
            safe_float(r["pct"]),
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, cod_dpto, grupo_etnico, causa, valor, pct)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    # 10 - limitacion_ppal_etnia_dpto
    table = "cnpv.limitacion_ppal_etnia_dpto"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "10_lim_ppal_x_etnia_dpto.csv")
    data = []
    for r in rows:
        data.append((
            "2018",
            pad_divipola(r["cod_dpto"], 2),
            r["grupo_etnico"],
            r["limitacion"],
            safe_int(r["valor"]),
            safe_float(r["pct"]),
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, cod_dpto, grupo_etnico, limitacion, valor, pct)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    conn.commit()
    print("=== CNPV data loaded successfully ===")


# ---------------------------------------------------------------------------
# Step 2: Pueblo data (CSVs 11-20)
# ---------------------------------------------------------------------------
def load_pueblo(conn):
    print("\n=== STEP 2: Loading Pueblo data ===")
    cur = conn.cursor()

    # 11 - disc_nacional
    table = "pueblo.disc_nacional"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "11_disc_x_pueblo_nacional.csv")
    data = []
    for r in rows:
        data.append((
            "2018",
            r["codigo"].strip(),
            r["pueblo"],
            safe_int(r["con_discapacidad"]),
            safe_int(r["sin_discapacidad"]),
            safe_int(r["total"]),
            safe_float(r["prevalencia_pct"]),
            safe_float(r["tasa_x_1000"]),
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, cod_pueblo, pueblo, con_discapacidad, sin_discapacidad, total, prevalencia_pct, tasa_x_1000)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    # Also populate cat.pueblos_indigenas
    cur.execute("TRUNCATE TABLE cat.pueblos_indigenas CASCADE")
    cat_data = [(r["codigo"].strip(), r["pueblo"]) for r in rows]
    execute_values(cur, """
        INSERT INTO cat.pueblos_indigenas (cod_pueblo, nombre) VALUES %s
        ON CONFLICT (cod_pueblo) DO NOTHING
    """, cat_data)
    print(f"  cat.pueblos_indigenas: {len(cat_data)} rows")

    # 12 - pueblo_municipio
    table = "pueblo.pueblo_municipio"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "12_pueblo_x_municipio.csv")
    data = []
    for r in rows:
        data.append((
            "2018",
            pad_divipola(r["cod_mpio"], 5),
            r["cod_pueblo"].strip(),
            r["pueblo"],
            safe_int(r["poblacion"]),
            safe_float(r["pct_en_mpio"]),
            r.get("es_dominante", ""),
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, cod_mpio, cod_pueblo, pueblo, poblacion, pct_en_mpio, es_dominante)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    # 13 - pueblo_dominante_mpio
    table = "pueblo.pueblo_dominante_mpio"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "13_pueblo_dominante_x_municipio.csv")
    data = []
    for r in rows:
        data.append((
            "2018",
            pad_divipola(r["cod_mpio"], 5),
            r["pueblo_dominante"],
            safe_int(r["pob_dominante"]),
            safe_int(r["pob_total_indig"]),
            safe_float(r["pct_dominante"]),
            safe_int(r["n_pueblos"]),
            r["confianza"],
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, cod_mpio, pueblo_dominante, pob_dominante, pob_total_indig, pct_dominante, n_pueblos, confianza)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    # 14 - disc_dpto
    table = "pueblo.disc_dpto"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "14_disc_x_pueblo_x_dpto.csv")
    data = []
    for r in rows:
        data.append((
            "2018",
            pad_divipola(r["cod_dpto"], 2),
            r["cod_pueblo"].strip(),
            r["pueblo"],
            safe_int(r["con_discapacidad"]),
            safe_int(r["sin_discapacidad"]),
            safe_int(r["total"]),
            safe_float(r["tasa_x_1000"]),
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, cod_dpto, cod_pueblo, pueblo, con_discapacidad, sin_discapacidad, total, tasa_x_1000)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    # 15 - sexo_nacional
    table = "pueblo.sexo_nacional"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "15_sexo_x_pueblo_nacional.csv")
    data = []
    for r in rows:
        data.append((
            "2018",
            r["cod_pueblo"].strip(),
            r["pueblo"],
            safe_int(r["hombres"]),
            safe_int(r["mujeres"]),
            safe_int(r["total"]),
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, cod_pueblo, pueblo, hombres, mujeres, total)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    # 16 - edad_nacional
    table = "pueblo.edad_nacional"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "16_edad_x_pueblo_nacional.csv")
    data = []
    for r in rows:
        data.append((
            "2018",
            r["cod_pueblo"].strip(),
            r["pueblo"],
            r["grupo_edad"],
            safe_int(r["valor"]),
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, cod_pueblo, pueblo, grupo_edad, valor)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    # 17 - limitacion_nacional
    table = "pueblo.limitacion_nacional"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "17_limitacion_x_pueblo_nacional.csv")
    data = []
    for r in rows:
        data.append((
            "2018",
            r["cod_pueblo"].strip(),
            r["pueblo"],
            r["limitacion"],
            safe_int(r["valor"]),
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, cod_pueblo, pueblo, limitacion, valor)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    # 18 - enfermo_nacional
    table = "pueblo.enfermo_nacional"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "18_enfermo_x_pueblo_nacional.csv")
    data = []
    for r in rows:
        data.append((
            "2018",
            r["cod_pueblo"].strip(),
            r["pueblo"],
            safe_int(r["enfermo_si"]),
            safe_int(r["enfermo_no"]),
            safe_int(r["no_informa"]),
            safe_int(r["total"]),
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, cod_pueblo, pueblo, enfermo_si, enfermo_no, no_informa, total)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    # 19 - tratamiento_nacional
    table = "pueblo.tratamiento_nacional"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "19_tratamiento_x_pueblo_nacional.csv")
    data = []
    for r in rows:
        data.append((
            "2018",
            r["cod_pueblo"].strip(),
            r["pueblo"],
            r["tratamiento"],
            safe_int(r["valor"]),
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, cod_pueblo, pueblo, tratamiento, valor)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    # 20 - causa_nacional
    table = "pueblo.causa_nacional"
    truncate_and_report(cur, table)
    rows = read_semicolon_csv(BD_CONSOLIDADA / "20_causa_x_pueblo_nacional.csv")
    data = []
    for r in rows:
        data.append((
            "2018",
            r["cod_pueblo"].strip(),
            r["pueblo"],
            r["causa"],
            safe_int(r["valor"]),
        ))
    execute_values(cur, f"""
        INSERT INTO {table} (periodo, cod_pueblo, pueblo, causa, valor)
        VALUES %s ON CONFLICT DO NOTHING
    """, data)
    report_count(cur, table)

    conn.commit()
    print("=== Pueblo data loaded successfully ===")


# ---------------------------------------------------------------------------
# Step 3: External sources
# ---------------------------------------------------------------------------
def load_external(conn):
    print("\n=== STEP 3: Loading external sources ===")
    cur = conn.cursor()

    # RUV - hechos municipal (already cleaned, comma-separated with quotes)
    ruv_file = FUENTES_EXTERNAS / "RUV" / "ruv_hechos_municipal_indigena.csv"
    if ruv_file.exists():
        table = "ext.ruv_hechos_municipal"
        truncate_and_report(cur, table)
        with open(ruv_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            data = []
            for r in reader:
                cod_dpto = pad_divipola(r.get("cod_estado_depto", ""), 2)
                cod_mpio = pad_divipola(r.get("cod_ciudad_muni", ""), 5)
                data.append((
                    r.get("fecha_corte"),
                    cod_dpto,
                    r.get("estado_depto"),
                    cod_mpio,
                    r.get("ciudad_municipio"),
                    r.get("hecho"),
                    r.get("etnia"),
                    r.get("sexo"),
                    r.get("discapacidad"),
                    r.get("ciclo_vital"),
                    safe_int(r.get("per_ocu")),
                    safe_int(r.get("per_sa")),
                    safe_int(r.get("eventos")),
                ))
            execute_values(cur, f"""
                INSERT INTO {table}
                    (fecha_corte, cod_dpto, estado_depto, cod_mpio, ciudad_municipio,
                     hecho, etnia, sexo, discapacidad, ciclo_vital,
                     per_ocu, per_sa, eventos)
                VALUES %s ON CONFLICT DO NOTHING
            """, data)
        report_count(cur, table)
    else:
        print(f"  SKIP: {ruv_file} not found")

    # ICBF beneficiarios
    icbf_file = FUENTES_EXTERNAS / "ICBF" / "icbf_beneficiarios_disc.csv"
    if icbf_file.exists():
        table = "ext.icbf_beneficiarios"
        truncate_and_report(cur, table)
        with open(icbf_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            data = []
            for r in reader:
                data.append((
                    safe_int(r.get("a_o") or r.get("año")),
                    pad_divipola(r.get("codigo_departamento_atenci") or r.get("codigo_departamento_atencion", ""), 2),
                    r.get("departamento_atenci_n") or r.get("departamento_atencion"),
                    pad_divipola(r.get("codigo_municipio_atenci_n") or r.get("codigo_municipio_atencion", ""), 5),
                    r.get("municipio_atenci_n") or r.get("municipio_atencion"),
                    r.get("area_misional"),
                    r.get("nombre_servicio"),
                    r.get("rango_edad"),
                    r.get("sexo"),
                    r.get("zona_ubicacion_beneficiario") or r.get("zona_ubicacion"),
                    r.get("agrupaci_n_etnica") or r.get("agrupacion_etnica"),
                    r.get("grupo_etnico"),
                    r.get("presenta_discapacidad"),
                    r.get("v_ctima") or r.get("victima"),
                    r.get("tipo_beneficiario_homologado") or r.get("tipo_beneficiario"),
                    safe_int(r.get("beneficiarios")),
                ))
            execute_values(cur, f"""
                INSERT INTO {table}
                    (anio, cod_dpto, departamento, cod_mpio, municipio,
                     area_misional, nombre_servicio, rango_edad, sexo,
                     zona_ubicacion, agrupacion_etnica, grupo_etnico,
                     presenta_discapacidad, victima, tipo_beneficiario,
                     beneficiarios)
                VALUES %s ON CONFLICT DO NOTHING
            """, data)
        report_count(cur, table)
    else:
        print(f"  SKIP: {icbf_file} not found")

    # RLCPD nacional
    rlcpd_file = FUENTES_EXTERNAS / "RLCPD" / "rlcpd_nacional.csv"
    if rlcpd_file.exists():
        table = "ext.rlcpd_nacional"
        truncate_and_report(cur, table)
        with open(rlcpd_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            data = []
            for r in reader:
                # Parse cod_mpio from "05001 - Medellin" format
                mpio_raw = r.get("municipioregistro", "")
                cod_mpio = None
                if mpio_raw and " - " in mpio_raw:
                    cod_mpio = pad_divipola(mpio_raw.split(" - ")[0].strip(), 5)

                fecha = r.get("fecharegistro", "")
                if fecha and "T" in fecha:
                    fecha = fecha.split("T")[0]
                if not fecha:
                    fecha = None

                data.append((
                    r.get("departamentoregistro"),
                    r.get("municipioregistro"),
                    cod_mpio,
                    fecha,
                    r.get("tipoalteracion"),
                    safe_int(r.get("numpersonas")),
                ))
            execute_values(cur, f"""
                INSERT INTO {table}
                    (departamento_registro, municipio_registro, cod_mpio_parsed,
                     fecha_registro, tipo_alteracion, num_personas)
                VALUES %s ON CONFLICT DO NOTHING
            """, data)
        report_count(cur, table)
    else:
        print(f"  SKIP: {rlcpd_file} not found")

    # Familias en Accion
    fa_file = FUENTES_EXTERNAS / "SISBEN" / "familias_accion_indigena_disc.csv"
    if fa_file.exists():
        table = "ext.familias_accion"
        truncate_and_report(cur, table)
        with open(fa_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            data = []
            for r in reader:
                data.append((
                    pad_divipola(r.get("codigodepartamentoatencion", ""), 2),
                    r.get("nombredepartamentoatencion"),
                    pad_divipola(r.get("codigomunicipioatencion", ""), 5),
                    r.get("nombremunicipioatencion"),
                    r.get("etnia"),
                    r.get("discapacidad"),
                    r.get("genero"),
                    r.get("rangoedad"),
                    r.get("tipopoblacion"),
                    safe_int(r.get("cantidaddebeneficiarios")),
                ))
            execute_values(cur, f"""
                INSERT INTO {table}
                    (cod_dpto, departamento, cod_mpio, municipio,
                     etnia, discapacidad, genero, rango_edad,
                     tipo_poblacion, beneficiarios)
                VALUES %s ON CONFLICT DO NOTHING
            """, data)
        report_count(cur, table)
    else:
        print(f"  SKIP: {fa_file} not found")

    conn.commit()
    print("=== External sources loaded successfully ===")


# ---------------------------------------------------------------------------
# Step 4: Victims data
# ---------------------------------------------------------------------------
def load_victimas(conn):
    print("\n=== STEP 4: Loading victims data ===")
    # Delegate to the dedicated loader
    from scripts.load_victimas import load_victimas_universo
    load_victimas_universo(conn)
    print("=== Victims data loaded successfully ===")


# ---------------------------------------------------------------------------
# Step 5: Recalculate indicators
# ---------------------------------------------------------------------------
def load_indicadores(conn):
    print("\n=== STEP 5: Recalculating indicators ===")
    cur = conn.cursor()
    cur.execute("SELECT indicadores.calcular_todos('2018')")
    n = cur.fetchone()[0]
    conn.commit()
    print(f"  Indicators recalculated: {n} records generated/updated")
    report_count(cur, "indicadores.valores")
    print("=== Indicators done ===")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
STEPS = {
    "cnpv": load_cnpv,
    "pueblo": load_pueblo,
    "ext": load_external,
    "victimas": load_victimas,
    "indicadores": load_indicadores,
}


def main():
    parser = argparse.ArgumentParser(description="SMT-ONIC data loader")
    parser.add_argument(
        "--step",
        choices=list(STEPS.keys()),
        help="Run only a specific step (default: all)",
    )
    args = parser.parse_args()

    conn = get_conn()
    print(f"Connected to: {DATABASE_URL_SYNC.split('@')[1] if '@' in DATABASE_URL_SYNC else DATABASE_URL_SYNC}")

    t0 = time.time()

    if args.step:
        STEPS[args.step](conn)
    else:
        for step_name, step_fn in STEPS.items():
            try:
                step_fn(conn)
            except Exception as e:
                print(f"\n  ERROR in step '{step_name}': {e}")
                conn.rollback()
                print("  Continuing with next step...")

    elapsed = time.time() - t0
    print(f"\nTotal time: {elapsed:.1f}s")
    conn.close()


if __name__ == "__main__":
    main()
