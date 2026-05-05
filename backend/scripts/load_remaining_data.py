"""
Load remaining datasets into SMT-ONIC PostgreSQL database.
TASK 1: CG2005 Censo data into cnpv schema
TASK 2: SMT-ONIC characterization summary into smt schema
"""

import csv
import psycopg2
from psycopg2.extras import execute_values

DB_CFG = dict(
    host="localhost",
    port=5450,
    user="smt_admin",
    password="smt_onic_2026",
    dbname="smt_onic",
)

CSV_DIR = "C:/Users/wilso/Desktop/discapacidad/bd_consolidada"


def read_csv(filename, sep=";"):
    """Read a semicolon-delimited CSV and return list of dicts."""
    path = f"{CSV_DIR}/{filename}"
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=sep)
        return list(reader)


def connect():
    conn = psycopg2.connect(**DB_CFG)
    conn.autocommit = False
    return conn


# ─────────────────────────────────────────────────────────
# TASK 1A: CG2005_01 → cnpv.resumen_nacional_etnico
# The CSV has grupo_etnico;tiene_limitacion;valor;periodo
# We need the "SI" rows → these are the pob_disc values
# And the "Total" rows → these are pob_total
# Then compute prevalencia and tasa.
# ─────────────────────────────────────────────────────────
def load_resumen_nacional(conn):
    """Load CG2005_01 into cnpv.resumen_nacional_etnico (periodo='2005')."""
    rows = read_csv("CG2005_01_limitacion_x_etnia_nacional.csv")

    # Build lookup: grupo_etnico → {SI: val, Total: val}
    lookup = {}
    for r in rows:
        ge = r["grupo_etnico"]
        lim = r["tiene_limitacion"]
        val = int(r["valor"])
        if ge not in lookup:
            lookup[ge] = {}
        lookup[ge][lim] = val

    cur = conn.cursor()

    # Delete existing 2005 rows if any (idempotent)
    cur.execute("DELETE FROM cnpv.resumen_nacional_etnico WHERE periodo = '2005'")
    deleted = cur.rowcount
    print(f"  resumen_nacional_etnico: deleted {deleted} existing 2005 rows")

    insert_sql = """
        INSERT INTO cnpv.resumen_nacional_etnico
            (periodo, grupo_etnico, pob_total, pob_disc, prevalencia_pct, tasa_x_1000)
        VALUES %s
    """
    values = []
    for ge, data in lookup.items():
        pob_total = data.get("Total", 0)
        pob_disc = data.get("SI", 0)
        prev = round(pob_disc / pob_total * 100, 2) if pob_total else 0
        tasa = round(pob_disc / pob_total * 1000, 2) if pob_total else 0
        values.append(("2005", ge, pob_total, pob_disc, prev, tasa))

    execute_values(cur, insert_sql, values)
    print(f"  resumen_nacional_etnico: inserted {len(values)} rows for 2005")

    # Verify total count
    cur.execute("SELECT COUNT(*), periodo FROM cnpv.resumen_nacional_etnico GROUP BY periodo ORDER BY periodo")
    for r in cur.fetchall():
        print(f"    periodo={r[1]}: {r[0]} rows")


# ─────────────────────────────────────────────────────────
# TASK 1B: CG2005_02 → cnpv.prevalencia_etnia_dpto
# CSV: cod_dpto;nom_dpto;grupo_etnico;con_limitacion;sin_limitacion;total;prevalencia_pct;tasa_x_1000;periodo
# Table: periodo, cod_dpto, grupo_etnico, pob_total, pob_disc, pob_no_disc, tasa_x_1000, prevalencia_pct
# ─────────────────────────────────────────────────────────
def load_prevalencia_dpto(conn):
    """Load CG2005_02 into cnpv.prevalencia_etnia_dpto (periodo='2005')."""
    rows = read_csv("CG2005_02_limitacion_x_etnia_x_dpto.csv")
    cur = conn.cursor()

    cur.execute("DELETE FROM cnpv.prevalencia_etnia_dpto WHERE periodo = '2005'")
    deleted = cur.rowcount
    print(f"  prevalencia_etnia_dpto: deleted {deleted} existing 2005 rows")

    insert_sql = """
        INSERT INTO cnpv.prevalencia_etnia_dpto
            (periodo, cod_dpto, grupo_etnico, pob_total, pob_disc, pob_no_disc, tasa_x_1000, prevalencia_pct)
        VALUES %s
    """
    values = []
    for r in rows:
        values.append((
            "2005",
            r["cod_dpto"],
            r["grupo_etnico"],
            int(r["total"]),
            int(r["con_limitacion"]),
            int(r["sin_limitacion"]),
            float(r["tasa_x_1000"]),
            float(r["prevalencia_pct"]),
        ))

    execute_values(cur, insert_sql, values)
    print(f"  prevalencia_etnia_dpto: inserted {len(values)} rows for 2005")


# ─────────────────────────────────────────────────────────
# TASK 1C: CG2005_03 → cnpv.salud_etnia_dpto as enfermo variable
# CSV: grupo_etnico;enfermo_si;enfermo_no;no_informa;total;pct_enfermo;periodo
# Table: periodo, cod_dpto, grupo_etnico, variable, categoria, valor, pct, total_grupo
# National-level → cod_dpto = '00'
# ─────────────────────────────────────────────────────────
def load_salud_enfermo(conn):
    """Load CG2005_03 into cnpv.salud_etnia_dpto as 'enfermo' variable."""
    rows = read_csv("CG2005_03_enfermo_x_etnia.csv")
    cur = conn.cursor()

    # Delete existing 2005 enfermo rows
    cur.execute("DELETE FROM cnpv.salud_etnia_dpto WHERE periodo = '2005' AND variable = 'enfermo'")
    deleted = cur.rowcount
    print(f"  salud_etnia_dpto (enfermo): deleted {deleted} existing 2005 rows")

    insert_sql = """
        INSERT INTO cnpv.salud_etnia_dpto
            (periodo, cod_dpto, grupo_etnico, variable, categoria, valor, pct, total_grupo)
        VALUES %s
    """
    values = []
    for r in rows:
        total = int(r["total"])
        ge = r["grupo_etnico"]

        # Insert each category as a separate row
        for cat, col in [("Si", "enfermo_si"), ("No", "enfermo_no"), ("No_informa", "no_informa")]:
            val = int(r[col])
            pct = round(val / total * 100, 2) if total else 0
            values.append(("2005", "00", ge, "enfermo", cat, val, pct, total))

    execute_values(cur, insert_sql, values)
    print(f"  salud_etnia_dpto (enfermo): inserted {len(values)} rows for 2005")


# ─────────────────────────────────────────────────────────
# TASK 1D: CG2005_09 → cnpv.disc_edad_dpto
# CSV: grupo_etnico;grupo_edad;valor;periodo
# Table: periodo, cod_dpto, grupo_edad, discapacidad, valor
# The 2005 data is by ethnicity (not dpto), so we use cod_dpto='00'
# and put grupo_etnico in the discapacidad column.
# ─────────────────────────────────────────────────────────
def load_edad_etnia(conn):
    """Load CG2005_09 into cnpv.disc_edad_dpto (periodo='2005')."""
    rows = read_csv("CG2005_09_edad_x_etnia.csv")
    cur = conn.cursor()

    cur.execute("DELETE FROM cnpv.disc_edad_dpto WHERE periodo = '2005'")
    deleted = cur.rowcount
    print(f"  disc_edad_dpto: deleted {deleted} existing 2005 rows")

    insert_sql = """
        INSERT INTO cnpv.disc_edad_dpto
            (periodo, cod_dpto, grupo_edad, discapacidad, valor)
        VALUES %s
    """
    values = []
    for r in rows:
        values.append((
            "2005",
            "00",  # national level
            r["grupo_edad"],
            r["grupo_etnico"],  # using grupo_etnico as the category dimension
            int(r["valor"]),
        ))

    execute_values(cur, insert_sql, values)
    print(f"  disc_edad_dpto: inserted {len(values)} rows for 2005")


# ─────────────────────────────────────────────────────────
# TASK 1E: CG2005_10 → cnpv.disc_sexo_dpto
# CSV: grupo_etnico;sexo;valor;periodo
# Table: periodo, cod_dpto, sexo, discapacidad, valor
# Same approach: cod_dpto='00', grupo_etnico → discapacidad
# ─────────────────────────────────────────────────────────
def load_sexo_etnia(conn):
    """Load CG2005_10 into cnpv.disc_sexo_dpto (periodo='2005')."""
    rows = read_csv("CG2005_10_sexo_x_etnia.csv")
    cur = conn.cursor()

    cur.execute("DELETE FROM cnpv.disc_sexo_dpto WHERE periodo = '2005'")
    deleted = cur.rowcount
    print(f"  disc_sexo_dpto: deleted {deleted} existing 2005 rows")

    insert_sql = """
        INSERT INTO cnpv.disc_sexo_dpto
            (periodo, cod_dpto, sexo, discapacidad, valor)
        VALUES %s
    """
    values = []
    for r in rows:
        values.append((
            "2005",
            "00",  # national level
            r["sexo"],
            r["grupo_etnico"],  # using grupo_etnico as the category dimension
            int(r["valor"]),
        ))

    execute_values(cur, insert_sql, values)
    print(f"  disc_sexo_dpto: inserted {len(values)} rows for 2005")


# ─────────────────────────────────────────────────────────
# TASK 1F: CG2005_COMPARACION_INTERCENSAL → cnpv.comparacion_intercensal
# CSV: grupo_etnico;periodo;pob_total;pob_con_cap_diversas;prevalencia_pct;tasa_x_1000
# ─────────────────────────────────────────────────────────
def load_comparacion_intercensal(conn):
    """Create table and load CG2005_COMPARACION_INTERCENSAL."""
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cnpv.comparacion_intercensal (
            id SERIAL PRIMARY KEY,
            grupo_etnico VARCHAR(50),
            periodo VARCHAR(10),
            pob_total BIGINT,
            pob_disc INTEGER,
            prevalencia_pct NUMERIC(6,2),
            tasa_x_1000 NUMERIC(8,2)
        )
    """)
    print("  comparacion_intercensal: table ensured")

    cur.execute("DELETE FROM cnpv.comparacion_intercensal")
    deleted = cur.rowcount
    print(f"  comparacion_intercensal: deleted {deleted} existing rows")

    rows = read_csv("CG2005_COMPARACION_INTERCENSAL.csv")
    insert_sql = """
        INSERT INTO cnpv.comparacion_intercensal
            (grupo_etnico, periodo, pob_total, pob_disc, prevalencia_pct, tasa_x_1000)
        VALUES %s
    """
    values = []
    for r in rows:
        values.append((
            r["grupo_etnico"],
            r["periodo"],
            int(r["pob_total"]),
            int(r["pob_con_cap_diversas"]),
            float(r["prevalencia_pct"]),
            float(r["tasa_x_1000"]),
        ))

    execute_values(cur, insert_sql, values)
    print(f"  comparacion_intercensal: inserted {len(values)} rows")


# ─────────────────────────────────────────────────────────
# TASK 2: SMT-ONIC characterization → smt.resumen
# ─────────────────────────────────────────────────────────
def load_smt_resumen(conn):
    """Create smt.resumen table and load dashboard data."""
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS smt.resumen (
            id SERIAL PRIMARY KEY,
            periodo VARCHAR(10) DEFAULT '2026-F1',
            dimension VARCHAR(50),
            categoria VARCHAR(100),
            valor NUMERIC(10,2),
            pct NUMERIC(6,2),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    print("  smt.resumen: table ensured")

    cur.execute("DELETE FROM smt.resumen WHERE periodo = '2026-F1'")
    deleted = cur.rowcount
    print(f"  smt.resumen: deleted {deleted} existing 2026-F1 rows")

    insert_sql = """
        INSERT INTO smt.resumen (periodo, dimension, categoria, valor, pct)
        VALUES %s
    """
    values = []

    # POR_REGION
    for item in [
        ("Occidente", 669, 64.1),
        ("Amazonia", 141, 13.5),
        ("Orinoquia", 117, 11.2),
        ("Norte", 94, 9.0),
        ("Oriente", 23, 2.2),
    ]:
        values.append(("2026-F1", "region", item[0], item[1], item[2]))

    # POR_SEXO
    for item in [
        ("Masculino", 460, 44.1),
        ("Femenino", 338, 32.4),
        ("Sin especificar", 246, 23.6),
    ]:
        values.append(("2026-F1", "sexo", item[0], item[1], item[2]))

    # POR_DISCAPACIDAD  (no pct in source, compute from total 1044)
    for item in [
        ("Fisica / Motora", 275),
        ("Visual", 190),
        ("Mental / Cognitiva", 132),
        ("Multiple", 96),
        ("Auditiva / Sensorial", 70),
        ("Desarmon. Espiritual", 10),
        ("Sin clasificar", 271),
    ]:
        pct = round(item[1] / 1044 * 100, 1)
        values.append(("2026-F1", "tipo_discapacidad", item[0], item[1], pct))

    # POR_EDAD (no pct in source, compute from total 1044 - but 907 summed, some missing)
    total_edad = 24 + 90 + 75 + 139 + 139 + 158 + 200 + 82  # = 907
    for item in [
        ("0-5", 24),
        ("6-12", 90),
        ("13-18", 75),
        ("19-30", 139),
        ("31-45", 139),
        ("46-60", 158),
        ("61-80", 200),
        ("80+", 82),
    ]:
        pct = round(item[1] / 1044 * 100, 1)
        values.append(("2026-F1", "edad", item[0], item[1], pct))

    # CERTIFICADO
    for item in [
        ("Sin certificado", 202),
        ("Con certificado", 138),
        ("Sin dato", 704),
    ]:
        pct = round(item[1] / 1044 * 100, 1)
        values.append(("2026-F1", "certificado", item[0], item[1], pct))

    # ORIGEN
    for item in [
        ("Adquirida", 224),
        ("Congenita", 153),
        ("Sin dato", 667),
    ]:
        pct = round(item[1] / 1044 * 100, 1)
        values.append(("2026-F1", "origen", item[0], item[1], pct))

    # CUIDADOR
    for item in [
        ("Con cuidador", 295),
        ("Sin cuidador", 75),
        ("Sin dato", 674),
    ]:
        pct = round(item[1] / 1044 * 100, 1)
        values.append(("2026-F1", "cuidador", item[0], item[1], pct))

    # CALIDAD_DATOS
    for item in [
        ("Certificado discapacidad", 67.4, "critico"),
        ("Cuidador", 64.6, "critico"),
        ("Origen", 63.9, "critico"),
        ("Barreras territorio", 81.2, "critico"),
        ("Tipo discapacidad", 25.0, "medio"),
        ("Sexo", 23.6, "medio"),
        ("Pueblo indigena", 8.3, "bajo"),
        ("Region / Org.", 0.0, "optimo"),
    ]:
        values.append(("2026-F1", "calidad", item[0], item[1], None))

    execute_values(cur, insert_sql, values)
    print(f"  smt.resumen: inserted {len(values)} rows for 2026-F1")


# ─────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────
def main():
    conn = connect()
    try:
        print("\n=== TASK 1: Loading Censo 2005 data ===")

        print("\n[1A] CG2005_01 -> cnpv.resumen_nacional_etnico")
        load_resumen_nacional(conn)

        print("\n[1B] CG2005_02 -> cnpv.prevalencia_etnia_dpto")
        load_prevalencia_dpto(conn)

        print("\n[1C] CG2005_03 -> cnpv.salud_etnia_dpto (enfermo)")
        load_salud_enfermo(conn)

        print("\n[1D] CG2005_09 -> cnpv.disc_edad_dpto")
        load_edad_etnia(conn)

        print("\n[1E] CG2005_10 -> cnpv.disc_sexo_dpto")
        load_sexo_etnia(conn)

        print("\n[1F] CG2005_COMPARACION_INTERCENSAL -> cnpv.comparacion_intercensal")
        load_comparacion_intercensal(conn)

        print("\n=== TASK 2: Loading SMT-ONIC characterization summary ===")
        load_smt_resumen(conn)

        conn.commit()
        print("\n*** All data committed successfully ***")

        # ── Verification ──
        print("\n=== VERIFICATION ===")
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM cnpv.comparacion_intercensal")
        cnt = cur.fetchone()[0]
        print(f"  cnpv.comparacion_intercensal: {cnt} rows (expected 16)")

        cur.execute("SELECT COUNT(*), periodo FROM cnpv.resumen_nacional_etnico GROUP BY periodo ORDER BY periodo")
        for r in cur.fetchall():
            print(f"  cnpv.resumen_nacional_etnico periodo={r[1]}: {r[0]} rows")
        cur.execute("SELECT COUNT(*) FROM cnpv.resumen_nacional_etnico")
        cnt = cur.fetchone()[0]
        print(f"  cnpv.resumen_nacional_etnico TOTAL: {cnt} rows (expected 16+)")

        cur.execute("SELECT COUNT(*) FROM smt.resumen WHERE periodo = '2026-F1'")
        cnt = cur.fetchone()[0]
        print(f"  smt.resumen (2026-F1): {cnt} rows (expected ~50)")

        cur.execute("SELECT COUNT(*), periodo FROM cnpv.prevalencia_etnia_dpto GROUP BY periodo ORDER BY periodo")
        for r in cur.fetchall():
            print(f"  cnpv.prevalencia_etnia_dpto periodo={r[1]}: {r[0]} rows")

        cur.execute("SELECT COUNT(*) FROM cnpv.disc_edad_dpto WHERE periodo = '2005'")
        cnt = cur.fetchone()[0]
        print(f"  cnpv.disc_edad_dpto (2005): {cnt} rows")

        cur.execute("SELECT COUNT(*) FROM cnpv.disc_sexo_dpto WHERE periodo = '2005'")
        cnt = cur.fetchone()[0]
        print(f"  cnpv.disc_sexo_dpto (2005): {cnt} rows")

        cur.execute("SELECT COUNT(*) FROM cnpv.salud_etnia_dpto WHERE periodo = '2005' AND variable = 'enfermo'")
        cnt = cur.fetchone()[0]
        print(f"  cnpv.salud_etnia_dpto (2005, enfermo): {cnt} rows")

    except Exception as e:
        conn.rollback()
        print(f"\n!!! ERROR: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
