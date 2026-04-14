"""
Procesa microdatos Antioquia CNPV 2018.
JOIN: Personas (indigenas) + Viviendas + MGN (codigo geografico).
Carga a PostgreSQL tabla cnpv.microdatos_personas_indigenas.
"""
import csv, sys, os
import psycopg2
from psycopg2.extras import execute_values

sys.stdout.reconfigure(encoding='utf-8')

DB_URL = "postgresql://smt_admin:smt_onic_2026@localhost:5450/smt_onic"
BASE = "D:/1.Programacion/1.onic-smt-dashboard/microdatos_cnpv2018/05Antioquia"

def safe_int(v):
    try:
        return int(v) if v and v.strip() else None
    except (ValueError, AttributeError):
        return None

def main():
    print("=" * 60)
    print("  MICRODATOS ANTIOQUIA — JOIN Personas + Viviendas + MGN")
    print("=" * 60)

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # Create table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cnpv.microdatos_personas_indigenas (
            id SERIAL PRIMARY KEY,
            u_dpto VARCHAR(2),
            u_mpio VARCHAR(5),
            ua_clase SMALLINT,
            cod_encuestas VARCHAR(20),
            u_vivienda VARCHAR(10),
            p_nrohog SMALLINT,
            p_nro_per SMALLINT,
            p_sexo SMALLINT,
            p_edadr SMALLINT,
            p_parentescor SMALLINT,
            pa1_grp_etnic SMALLINT,
            pa11_cod_etnia VARCHAR(5),
            pa_habla_leng SMALLINT,
            pa1_entiende SMALLINT,
            p_enfermo SMALLINT,
            p_quehizo_ppal SMALLINT,
            pa_lo_atendieron SMALLINT,
            pa1_calidad_serv SMALLINT,
            condicion_fisica SMALLINT,
            p_alfabeta SMALLINT,
            pa_asistencia SMALLINT,
            p_nivel_anosr SMALLINT,
            p_trabajo SMALLINT,
            p_est_civil SMALLINT,
            uva2_codter VARCHAR(10),
            v_tipo_viv SMALLINT,
            va_ee SMALLINT,
            vb_acu SMALLINT,
            vc_alc SMALLINT,
            vf_internet SMALLINT,
            cod_dane_anm VARCHAR(30),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    conn.commit()

    # Step 1: Index viviendas
    print("\n1. Indexando viviendas...")
    viv = {}
    with open(f"{BASE}/CNPV2018_1VIV_A2_05.CSV", "r", encoding="latin-1") as f:
        for row in csv.DictReader(f):
            k = f"{row['U_DPTO']}_{row['U_MPIO']}_{row['COD_ENCUESTAS']}_{row['U_VIVIENDA']}"
            viv[k] = {
                "uva2": row.get("UVA2_CODTER", "").strip() or None,
                "vtip": safe_int(row.get("V_TIPO_VIV")),
                "ee": safe_int(row.get("VA_EE")),
                "acu": safe_int(row.get("VB_ACU")),
                "alc": safe_int(row.get("VC_ALC")),
                "int": safe_int(row.get("VF_INTERNET")),
            }
    print(f"   {len(viv):,} viviendas")

    # Step 2: Index MGN
    print("2. Indexando MGN...")
    mgn = {}
    with open(f"{BASE}/CNPV2018_MGN_A2_05.CSV", "r", encoding="latin-1") as f:
        for row in csv.DictReader(f):
            k = f"{row['U_DPTO']}_{row['U_MPIO']}_{row['COD_ENCUESTAS']}_{row['U_VIVIENDA']}"
            mgn[k] = row.get("COD_DANE_ANM", "").strip() or None
    print(f"   {len(mgn):,} codigos MGN")

    # Step 3: Read personas, filter indigenous, join
    print("3. Procesando personas indigenas...")
    batch = []
    total = 0
    indigenas = 0

    with open(f"{BASE}/CNPV2018_5PER_A2_05.CSV", "r", encoding="latin-1") as f:
        for row in csv.DictReader(f):
            total += 1
            if row.get("PA1_GRP_ETNIC") != "1":
                continue
            indigenas += 1

            k = f"{row['U_DPTO']}_{row['U_MPIO']}_{row['COD_ENCUESTAS']}_{row['U_VIVIENDA']}"
            v = viv.get(k, {})
            cod = mgn.get(k)

            batch.append((
                row["U_DPTO"].zfill(2),
                (row["U_DPTO"] + row["U_MPIO"]).zfill(5),
                safe_int(row.get("UA_CLASE")),
                row.get("COD_ENCUESTAS", ""),
                row.get("U_VIVIENDA", ""),
                safe_int(row.get("P_NROHOG")),
                safe_int(row.get("P_NRO_PER")),
                safe_int(row.get("P_SEXO")),
                safe_int(row.get("P_EDADR")),
                safe_int(row.get("P_PARENTESCOR")),
                1,
                row.get("PA11_COD_ETNIA", "").strip() or None,
                safe_int(row.get("PA_HABLA_LENG")),
                safe_int(row.get("PA1_ENTIENDE")),
                safe_int(row.get("P_ENFERMO")),
                safe_int(row.get("P_QUEHIZO_PPAL")),
                safe_int(row.get("PA_LO_ATENDIERON")),
                safe_int(row.get("PA1_CALIDAD_SERV")),
                safe_int(row.get("CONDICION_FISICA")),
                safe_int(row.get("P_ALFABETA")),
                safe_int(row.get("PA_ASISTENCIA")),
                safe_int(row.get("P_NIVEL_ANOSR")),
                safe_int(row.get("P_TRABAJO")),
                safe_int(row.get("P_EST_CIVIL")),
                v.get("uva2"),
                v.get("vtip"),
                v.get("ee"),
                v.get("acu"),
                v.get("alc"),
                v.get("int"),
                cod,
            ))

            if len(batch) >= 5000:
                execute_values(cur, """
                    INSERT INTO cnpv.microdatos_personas_indigenas
                    (u_dpto, u_mpio, ua_clase, cod_encuestas, u_vivienda,
                     p_nrohog, p_nro_per, p_sexo, p_edadr, p_parentescor,
                     pa1_grp_etnic, pa11_cod_etnia, pa_habla_leng, pa1_entiende,
                     p_enfermo, p_quehizo_ppal, pa_lo_atendieron,
                     pa1_calidad_serv, condicion_fisica, p_alfabeta, pa_asistencia,
                     p_nivel_anosr, p_trabajo, p_est_civil,
                     uva2_codter, v_tipo_viv, va_ee, vb_acu, vc_alc, vf_internet,
                     cod_dane_anm)
                    VALUES %s
                """, batch)
                conn.commit()
                batch = []

            if total % 1000000 == 0:
                print(f"   {total:,} leidas | {indigenas:,} indigenas")

    if batch:
        execute_values(cur, """
            INSERT INTO cnpv.microdatos_personas_indigenas
            (u_dpto, u_mpio, ua_clase, cod_encuestas, u_vivienda,
             p_nrohog, p_nro_per, p_sexo, p_edadr, p_parentescor,
             pa1_grp_etnic, pa11_cod_etnia, pa_habla_leng, pa1_entiende,
             p_enfermo, p_quehizo_ppal, pa_lo_atendieron,
             pa1_calidad_serv, condicion_fisica, p_alfabeta, pa_asistencia,
             p_nivel_anosr, p_trabajo, p_est_civil,
             uva2_codter, v_tipo_viv, va_ee, vb_acu, vc_alc, vf_internet,
             cod_dane_anm)
            VALUES %s
        """, batch)
        conn.commit()

    # Stats
    cur.execute("SELECT COUNT(*) FROM cnpv.microdatos_personas_indigenas WHERE u_dpto='05'")
    n = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT pa11_cod_etnia) FROM cnpv.microdatos_personas_indigenas WHERE u_dpto='05' AND pa11_cod_etnia IS NOT NULL")
    p = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM cnpv.microdatos_personas_indigenas WHERE u_dpto='05' AND condicion_fisica=1")
    d = cur.fetchone()[0]

    cur.close()
    conn.close()

    print(f"\n{'='*60}")
    print(f"  ANTIOQUIA COMPLETADO")
    print(f"  Total leidas: {total:,}")
    print(f"  Indigenas cargados: {n:,}")
    print(f"  Pueblos: {p}")
    print(f"  Con cap. diversas: {d:,}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
