"""
Carga SOLO victimas indigenas con capacidades diversas del UNIVERSO RUV.
37,797 registros de 12.1M totales.
Imputa pueblo indigena usando pueblo.pueblo_dominante_mpio.
"""
import os
import sys
import re
from datetime import datetime
from collections import Counter

import psycopg2
from psycopg2.extras import execute_values

DB_URL = os.environ.get(
    "DATABASE_URL_SYNC",
    "postgresql://smt_admin:smt_onic_2026@localhost:5450/smt_onic",
)
UNIVERSO_PATH = os.environ.get(
    "UNIVERSO_PATH",
    "D:/1.Programacion/1.onic-smt-dashboard/victimas/0001_UNIVERSO_VICTIMAS_LB_ANONIMO.txt",
)
SEP = "\xbb"


def clean_disc_type(desc):
    """Clasifica DESCRIPCIONDISCAPACIDAD en categorias limpias."""
    d = (desc or "").upper().strip()
    if not d or d in ("NINGUNA", "-", "NO APLICA"):
        return "SIN_INFORMACION"
    if any(k in d for k in ("FISICA", "CAMINAR", "CORRER", "DESPLAZAR", "LLEVAR",
                             "CAMBIAR", "RESPIRAT", "CORAZON", "MANOS", "BRAZOS")):
        return "FISICA"
    if any(k in d for k in ("VISUAL", "VER", "LUZ", "GAFAS", "LENTES", "OBJETOS O PERSONA")):
        return "VISUAL"
    if any(k in d for k in ("AUDITIVA", "OIR", "HABLAR", "COMUNICAR", "SONIDO")):
        return "AUDITIVA"
    if any(k in d for k in ("INTELECTUAL", "PENSAR", "MEMORIZAR", "APRENDER")):
        return "INTELECTUAL"
    if any(k in d for k in ("PSICOSOCIAL", "MENTAL", "RELACION", "ENTORNO")):
        return "PSICOSOCIAL"
    if "MULTIPLE" in d:
        return "MULTIPLE"
    return "SIN_INFORMACION"


def parse_date(s):
    """Parse DD/MM/YYYY date string."""
    if not s or s.strip() in ("", "01/01/1900"):
        return None
    try:
        return datetime.strptime(s.strip()[:10], "%d/%m/%Y").date()
    except (ValueError, IndexError):
        return None


def pad_mpio(code):
    """Normalize DIVIPOLA municipality code to 5 digits."""
    if not code:
        return None
    c = str(code).strip().replace(".0", "")
    if not c or not c.isdigit() or c == "0":
        return None
    return c.zfill(5)


def main():
    print("=" * 65)
    print("  CARGA: Victimas indigenas con capacidades diversas")
    print("  Fuente: UNIVERSO RUV (12.1M -> filtro -> ~37K registros)")
    print("=" * 65)

    if not os.path.exists(UNIVERSO_PATH):
        print(f"ERROR: No se encuentra {UNIVERSO_PATH}")
        sys.exit(1)

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # Step 1: Load pueblo imputation lookup from PostgreSQL
    print("\n  Cargando tabla de imputacion de pueblo...")
    cur.execute("""
        SELECT cod_mpio, pueblo_dominante, pct_dominante, confianza
        FROM pueblo.pueblo_dominante_mpio
        WHERE periodo = '2018'
    """)
    pueblo_lookup = {}
    for cod_mpio, pueblo, pct, conf in cur.fetchall():
        pueblo_lookup[cod_mpio] = (pueblo, float(pct), conf)
    print(f"    {len(pueblo_lookup)} municipios con pueblo asignado")

    # Step 2: Read UNIVERSO and filter indigenous + disability
    print(f"\n  Leyendo {UNIVERSO_PATH}...")
    print(f"  Filtrando: PERTENENCIAETNICA IN ('INDIGENA','INDIGENA ACREDITADO RA') AND DISCAPACIDAD='1'")

    records = []
    total_read = 0
    total_indig = 0

    with open(UNIVERSO_PATH, "r", encoding="latin-1") as f:
        header = f.readline().strip().split(SEP)

        # Build column index map
        col = {h: i for i, h in enumerate(header)}

        for line in f:
            total_read += 1
            parts = line.strip().split(SEP)
            if len(parts) < 51:
                continue

            etnia = parts[col.get("PERTENENCIAETNICA", 14)].strip()
            disc = parts[col.get("DISCAPACIDAD", 49)].strip()

            if etnia not in ("INDIGENA", "INDIGENA ACREDITADO RA"):
                continue
            total_indig += 1

            if disc != "1":
                continue

            # Extract fields
            cod_mpio_ocu = pad_mpio(parts[col.get("CODDANEMUNICIPIOOCURRENCIA", 19)])
            cod_mpio_res = pad_mpio(parts[col.get("CODDANEMUNICIPIORESIDENCIA", 29)])
            desc_disc = parts[col.get("DESCRIPCIONDISCAPACIDAD", 50)].strip()
            tipo_limpia = clean_disc_type(desc_disc)

            # Impute pueblo based on municipality of occurrence
            pueblo_imp, pct_dom, confianza = None, None, None
            if cod_mpio_ocu and cod_mpio_ocu in pueblo_lookup:
                pueblo_imp, pct_dom, confianza = pueblo_lookup[cod_mpio_ocu]
            elif cod_mpio_res and cod_mpio_res in pueblo_lookup:
                pueblo_imp, pct_dom, confianza = pueblo_lookup[cod_mpio_res]

            records.append((
                parts[col.get("IDPERSONA", 3)].strip()[:20],
                etnia,
                parts[col.get("GENERO", 15)].strip()[:20],
                parse_date(parts[col.get("FECHANACIMIENTO", 11)]),
                parts[col.get("HECHO", 17)].strip()[:200],
                parse_date(parts[col.get("FECHAOCURRENCIA", 18)]),
                cod_mpio_ocu,
                cod_mpio_res,
                parts[col.get("ZONAOCURRENCIA", 20)].strip()[:30],
                parts[col.get("PRESUNTOACTOR", 22)].strip()[:100],
                parts[col.get("TIPOVICTIMA", 26)].strip()[:20],
                parts[col.get("ESTADOVICTIMA", 37)].strip()[:30],
                disc,
                desc_disc[:500] if desc_disc else None,
                tipo_limpia,
                pueblo_imp,
                confianza,
            ))

            if total_read % 2000000 == 0:
                print(f"    ... {total_read:,} leidos, {len(records):,} filtrados")

    print(f"\n  Lectura completa:")
    print(f"    Total leidos: {total_read:,}")
    print(f"    Indigenas: {total_indig:,}")
    print(f"    Con capacidades diversas: {len(records):,}")

    # Step 3: Insert into PostgreSQL
    print(f"\n  Insertando {len(records):,} registros en victimas.universo...")
    cur.execute("TRUNCATE TABLE victimas.universo CASCADE")

    # Insert in batches
    batch_size = 5000
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        execute_values(cur, """
            INSERT INTO victimas.universo
            (idpersona, pertenencia_etnica, genero, fecha_nacimiento,
             hecho, fecha_ocurrencia, cod_mpio_ocurrencia, cod_mpio_residencia,
             zona_ocurrencia, presunto_actor, tipo_victima, estado_victima,
             discapacidad, descripcion_discapacidad, tipo_discapacidad_limpia,
             pueblo_imputado, confianza_imputacion)
            VALUES %s
        """, batch)

    conn.commit()

    # Step 4: Verify and build summary
    cur.execute("SELECT COUNT(*) FROM victimas.universo")
    n_total = cur.fetchone()[0]
    print(f"    Insertados: {n_total:,} registros")

    # Build resumen_pueblo_hecho
    print(f"\n  Construyendo resumen por pueblo x hecho...")
    cur.execute("TRUNCATE TABLE victimas.resumen_pueblo_hecho CASCADE")
    cur.execute("""
        INSERT INTO victimas.resumen_pueblo_hecho
        (cod_pueblo_imputado, pueblo_imputado, hecho, tipo_disc_limpia,
         cod_dpto, cod_mpio, cantidad)
        SELECT
            NULL,
            pueblo_imputado,
            hecho,
            tipo_discapacidad_limpia,
            LEFT(cod_mpio_ocurrencia, 2),
            cod_mpio_ocurrencia,
            COUNT(*)
        FROM victimas.universo
        WHERE pueblo_imputado IS NOT NULL
        GROUP BY pueblo_imputado, hecho, tipo_discapacidad_limpia,
                 LEFT(cod_mpio_ocurrencia, 2), cod_mpio_ocurrencia
    """)
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM victimas.resumen_pueblo_hecho")
    n_resumen = cur.fetchone()[0]
    print(f"    Resumen: {n_resumen:,} filas agregadas")

    # Step 5: Print summary stats
    print(f"\n{'='*65}")
    print(f"  ESTADISTICAS FINALES")
    print(f"{'='*65}")

    cur.execute("""
        SELECT pueblo_imputado, COUNT(*) as n
        FROM victimas.universo
        WHERE pueblo_imputado IS NOT NULL
        GROUP BY pueblo_imputado
        ORDER BY n DESC LIMIT 15
    """)
    print(f"\n  Top 15 pueblos (imputados) con cap. diversas por conflicto:")
    for pueblo, n in cur.fetchall():
        print(f"    {pueblo:<30} {n:>6,}")

    cur.execute("""
        SELECT tipo_discapacidad_limpia, COUNT(*) as n
        FROM victimas.universo
        GROUP BY tipo_discapacidad_limpia
        ORDER BY n DESC
    """)
    print(f"\n  Por tipo de capacidad diversa:")
    for tipo, n in cur.fetchall():
        print(f"    {tipo:<20} {n:>6,}")

    cur.execute("""
        SELECT hecho, COUNT(*) as n
        FROM victimas.universo
        GROUP BY hecho
        ORDER BY n DESC LIMIT 10
    """)
    print(f"\n  Por hecho victimizante:")
    for hecho, n in cur.fetchall():
        print(f"    {hecho:<55} {n:>6,}")

    cur.execute("""
        SELECT confianza_imputacion, COUNT(*) as n
        FROM victimas.universo
        GROUP BY confianza_imputacion
        ORDER BY n DESC
    """)
    print(f"\n  Confianza de imputacion de pueblo:")
    for conf, n in cur.fetchall():
        print(f"    {str(conf):<10} {n:>6,}")

    cur.close()
    conn.close()
    print(f"\n  Carga completada exitosamente.")


if __name__ == "__main__":
    main()
