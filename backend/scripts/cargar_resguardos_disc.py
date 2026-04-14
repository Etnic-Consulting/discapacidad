"""
Carga datos reales de capacidades diversas por resguardo extraidos de REDATAM.
Se ejecuta despues de extraer_resguardos_redatam.py.
Tiene soporte para re-ejecucion (UPSERT).
"""
import csv
import os
import sys
import psycopg2

sys.stdout.reconfigure(encoding='utf-8')

DB_URL = "postgresql://smt_admin:smt_onic_2026@localhost:5450/smt_onic"
CSV_PATH = "C:/Users/wilso/Desktop/discapacidad/datos_extraidos/resguardo_real/disc_por_resguardo_TODOS.csv"


def main():
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: {CSV_PATH} no existe. Ejecute primero extraer_resguardos_redatam.py")
        sys.exit(1)

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # Read CSV
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        rows = list(reader)

    print(f"Registros en CSV: {len(rows)}")

    # Upsert each row
    inserted = 0
    for r in rows:
        try:
            cur.execute("""
                INSERT INTO cnpv.disc_resguardo
                (periodo, cod_resguardo, nombre_resguardo, pob_total_visor,
                 con_cap_diversas, sin_cap_diversas, total_evaluados, tasa_x_1000)
                VALUES ('2018', %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (periodo, cod_resguardo) DO UPDATE SET
                    nombre_resguardo = EXCLUDED.nombre_resguardo,
                    pob_total_visor = EXCLUDED.pob_total_visor,
                    con_cap_diversas = EXCLUDED.con_cap_diversas,
                    sin_cap_diversas = EXCLUDED.sin_cap_diversas,
                    total_evaluados = EXCLUDED.total_evaluados,
                    tasa_x_1000 = EXCLUDED.tasa_x_1000,
                    created_at = NOW()
            """, (
                r['cod_resguardo'],
                r['nombre_resguardo'],
                int(r['pob_total_visor']) if r['pob_total_visor'] else 0,
                int(r['con_cap_diversas']) if r['con_cap_diversas'] else 0,
                int(r['sin_cap_diversas']) if r['sin_cap_diversas'] else 0,
                int(r['total_evaluados']) if r['total_evaluados'] else 0,
                float(r['tasa_x_1000']) if r['tasa_x_1000'] else 0,
            ))
            inserted += 1
        except Exception as e:
            print(f"  Error en {r.get('cod_resguardo')}: {e}")

    conn.commit()

    # Verify
    cur.execute("SELECT COUNT(*), SUM(con_cap_diversas), AVG(tasa_x_1000) FROM cnpv.disc_resguardo")
    total, sum_disc, avg_tasa = cur.fetchone()
    print(f"\nCargados: {total} resguardos")
    print(f"Total con cap. diversas: {int(sum_disc):,}")
    print(f"Tasa promedio: {float(avg_tasa):.1f} por mil")

    # Top 10
    cur.execute("""
        SELECT nombre_resguardo, con_cap_diversas, total_evaluados, tasa_x_1000
        FROM cnpv.disc_resguardo
        WHERE total_evaluados >= 100
        ORDER BY con_cap_diversas DESC LIMIT 10
    """)
    print(f"\nTop 10 resguardos por personas con cap. diversas:")
    for r in cur.fetchall():
        print(f"  {r[0][:40]}: {r[1]:,} de {r[2]:,} ({r[3]} por mil)")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
