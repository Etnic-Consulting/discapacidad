"""
Procesa microdatos del CNPV 2018 y cruza con shapefile de viviendas.
Agrega variables de persona (capacidades diversas, salud, educacion, lengua)
a cada vivienda georreferenciada.

Prerequisito: descargar ZIPs de microdatos.dane.gov.co/index.php/catalog/643/get-microdata
Guardar en: D:/1.Programacion/1.onic-smt-dashboard/microdatos_cnpv2018/
"""
import os
import sys
import csv
import glob
import zipfile
import psycopg2
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

MICRODATOS_DIR = "D:/1.Programacion/1.onic-smt-dashboard/microdatos_cnpv2018"
DB_URL = "postgresql://smt_admin:smt_onic_2026@localhost:5450/smt_onic"


def create_tables(conn):
    """Create tables for enriched vivienda data."""
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cnpv.personas_indigenas (
            id SERIAL PRIMARY KEY,
            cod_dane_vivienda VARCHAR(30),
            u_dpto VARCHAR(2),
            u_mpio VARCHAR(5),
            p_sexo SMALLINT,
            p_edadr VARCHAR(10),
            pa1_grp_etnic SMALLINT,
            pa11_cod_etnia VARCHAR(5),
            condicion_fisica SMALLINT,
            p_lim_ppal SMALLINT,
            p_causa_lim SMALLINT,
            p_enfermo SMALLINT,
            p_quehizo_ppal SMALLINT,
            pa_lo_atendieron SMALLINT,
            p41b1alfab SMALLINT,
            p34bhablal SMALLINT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_pers_indig_dpto ON cnpv.personas_indigenas(u_dpto);
        CREATE INDEX IF NOT EXISTS idx_pers_indig_mpio ON cnpv.personas_indigenas(u_mpio);
        CREATE INDEX IF NOT EXISTS idx_pers_indig_pueblo ON cnpv.personas_indigenas(pa11_cod_etnia);
        CREATE INDEX IF NOT EXISTS idx_pers_indig_cod ON cnpv.personas_indigenas(cod_dane_vivienda);

        -- Aggregated per-vivienda statistics
        CREATE TABLE IF NOT EXISTS cnpv.vivienda_personas_resumen (
            id SERIAL PRIMARY KEY,
            cod_dane_vivienda VARCHAR(30) UNIQUE,
            u_dpto VARCHAR(2),
            u_mpio VARCHAR(5),
            total_personas INTEGER,
            total_indigenas INTEGER,
            total_con_disc INTEGER,
            total_hombres INTEGER,
            total_mujeres INTEGER,
            pueblo_dominante VARCHAR(5),
            pct_alfabetismo NUMERIC(5,1),
            pct_habla_lengua NUMERIC(5,1),
            pct_enfermo NUMERIC(5,1),
            lim_principal VARCHAR(50),
            causa_principal VARCHAR(50),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_viv_res_cod ON cnpv.vivienda_personas_resumen(cod_dane_vivienda);
    """)
    conn.commit()
    cur.close()


def safe_int(val):
    try:
        return int(val) if val and val.strip() else None
    except (ValueError, AttributeError):
        return None


def process_department(zip_path, conn):
    """Process one department ZIP file."""
    dpto = os.path.basename(zip_path).split('_')[0]
    print(f"  Procesando {os.path.basename(zip_path)}...")

    cur = conn.cursor()
    batch = []
    total_read = 0
    total_indigena = 0

    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Find the Personas file
        per_files = [f for f in zf.namelist() if '3PER' in f.upper() or 'PERSONA' in f.upper()]
        if not per_files:
            per_files = [f for f in zf.namelist() if f.endswith('.CSV') or f.endswith('.csv')]
            per_files = [f for f in per_files if 'PER' in f.upper()]

        if not per_files:
            print(f"    No se encontro archivo de personas en {zip_path}")
            return 0

        per_file = per_files[0]
        print(f"    Archivo: {per_file}")

        with zf.open(per_file) as f:
            import io
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='latin-1'))

            for row in reader:
                total_read += 1

                # Filter: only indigenous
                etnic = safe_int(row.get('PA1_GRP_ETNIC', row.get('pa1_grp_etnic', '')))
                if etnic != 1:
                    continue

                total_indigena += 1

                # Build vivienda code from geographic fields
                u_dpto = str(row.get('U_DPTO', row.get('u_dpto', ''))).strip().zfill(2)
                u_mpio = str(row.get('U_MPIO', row.get('u_mpio', ''))).strip().zfill(5)

                batch.append((
                    f"{u_dpto}_{u_mpio}",  # simplified vivienda code
                    u_dpto,
                    u_mpio,
                    safe_int(row.get('P_SEXO', row.get('p_sexo', ''))),
                    str(row.get('P_EDADR', row.get('p_edadr', ''))).strip(),
                    etnic,
                    str(row.get('PA11_COD_ETNIA', row.get('pa11_cod_etnia', ''))).strip(),
                    safe_int(row.get('CONDICION_FISICA', row.get('condicion_fisica', ''))),
                    safe_int(row.get('P_LIM_PPAL', row.get('p_lim_ppal', ''))),
                    safe_int(row.get('P_CAUSA_LIM', row.get('p_causa_lim', ''))),
                    safe_int(row.get('P_ENFERMO', row.get('p_enfermo', ''))),
                    safe_int(row.get('P_QUEHIZO_PPAL', row.get('p_quehizo_ppal', ''))),
                    safe_int(row.get('PA_LO_ATENDIERON', row.get('pa_lo_atendieron', ''))),
                    safe_int(row.get('P41B1ALFAB', row.get('p41b1alfab', ''))),
                    safe_int(row.get('P34BHABLAL', row.get('p34bhablal', ''))),
                ))

                if len(batch) >= 10000:
                    _insert_batch(cur, batch)
                    batch = []

                if total_read % 1000000 == 0:
                    print(f"    Leidos: {total_read:,} | Indigenas: {total_indigena:,}")

        if batch:
            _insert_batch(cur, batch)

    conn.commit()
    cur.close()
    print(f"    Total: {total_read:,} leidos, {total_indigena:,} indigenas cargados")
    return total_indigena


def _insert_batch(cur, batch):
    from psycopg2.extras import execute_values
    execute_values(cur, """
        INSERT INTO cnpv.personas_indigenas
        (cod_dane_vivienda, u_dpto, u_mpio, p_sexo, p_edadr, pa1_grp_etnic,
         pa11_cod_etnia, condicion_fisica, p_lim_ppal, p_causa_lim,
         p_enfermo, p_quehizo_ppal, pa_lo_atendieron, p41b1alfab, p34bhablal)
        VALUES %s
    """, batch)


def main():
    print("=" * 60)
    print("  PROCESAMIENTO DE MICRODATOS CNPV 2018")
    print("  Enriquecimiento de viviendas con variables de persona")
    print("=" * 60)

    if not os.path.exists(MICRODATOS_DIR):
        os.makedirs(MICRODATOS_DIR, exist_ok=True)
        print(f"\nCreado directorio: {MICRODATOS_DIR}")
        print(f"Descargue los ZIPs de microdatos.dane.gov.co/index.php/catalog/643/get-microdata")
        print(f"Guarde los archivos en: {MICRODATOS_DIR}")
        print(f"Luego ejecute este script de nuevo.")
        return

    zips = sorted(glob.glob(os.path.join(MICRODATOS_DIR, "*.zip")))
    if not zips:
        print(f"\nNo se encontraron archivos ZIP en {MICRODATOS_DIR}")
        print(f"Descargue los ZIPs de microdatos.dane.gov.co/index.php/catalog/643/get-microdata")
        return

    print(f"\nArchivos encontrados: {len(zips)}")
    for z in zips:
        print(f"  {os.path.basename(z)}")

    conn = psycopg2.connect(DB_URL)
    create_tables(conn)

    total_indigenas = 0
    for zip_path in zips:
        try:
            n = process_department(zip_path, conn)
            total_indigenas += n
        except Exception as e:
            print(f"  ERROR en {os.path.basename(zip_path)}: {e}")

    # Final stats
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM cnpv.personas_indigenas")
    total_db = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT pa11_cod_etnia) FROM cnpv.personas_indigenas")
    pueblos_db = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM cnpv.personas_indigenas WHERE condicion_fisica = 1")
    disc_db = cur.fetchone()[0]
    cur.close()
    conn.close()

    print(f"\n{'=' * 60}")
    print(f"  RESULTADO FINAL")
    print(f"  Personas indigenas cargadas: {total_db:,}")
    print(f"  Pueblos distintos: {pueblos_db}")
    print(f"  Con capacidades diversas: {disc_db:,}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
