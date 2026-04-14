"""
Extrae datos reales de capacidades diversas por resguardo desde REDATAM CNPV 2018.
Query: FREQUENCY Personas.CONDICION_FISICA WHERE PA1_GRP_ETNIC=1 AND UNIDAD.UVA2_CODTER={code}
Extrae TODOS los 855 resguardos.
"""
import os
import re
import csv
import time
import sys
import html as htmlmod
import requests

sys.stdout.reconfigure(encoding='utf-8')

REDATAM_URL = "https://systema59.dane.gov.co/bincol/RpWebStats.exe/CmdSet?"
OUTPUT_DIR = "C:/Users/wilso/Desktop/discapacidad/datos_extraidos/resguardo_real"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "disc_por_resguardo_TODOS.csv")
SLEEP_BETWEEN = 2  # seconds between queries

# Get all resguardo codes from PostgreSQL
import psycopg2
conn = psycopg2.connect("postgresql://smt_admin:smt_onic_2026@localhost:5450/smt_onic")
cur = conn.cursor()
cur.execute("""
    SELECT SUBSTRING(resguardo FROM '\((\d+)\)') as code,
           resguardo as nombre,
           SUM(poblacion) as pob_total
    FROM visor_dane.resguardo_pueblo
    WHERE poblacion > 0
    GROUP BY SUBSTRING(resguardo FROM '\((\d+)\)'), resguardo
    ORDER BY SUM(poblacion) DESC
""")
resguardos = [(r[0], r[1], r[2]) for r in cur.fetchall() if r[0]]
cur.close()
conn.close()

print(f"Total resguardos a extraer: {len(resguardos)}")
print(f"Tiempo estimado: {len(resguardos) * (SLEEP_BETWEEN + 3) / 60:.0f} minutos")
print(f"Salida: {OUTPUT_CSV}")
print()

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Resume support: check which codes we already have
existing_codes = set()
if os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            existing_codes.add(row['cod_resguardo'])
    print(f"Ya extraidos: {len(existing_codes)} (continuando desde donde quedo)")

# Open CSV for append
write_header = len(existing_codes) == 0
with open(OUTPUT_CSV, 'a' if existing_codes else 'w', encoding='utf-8', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=';')
    if write_header:
        writer.writerow(['cod_resguardo', 'nombre_resguardo', 'pob_total_visor', 'con_cap_diversas', 'sin_cap_diversas', 'total_evaluados', 'tasa_x_1000'])

    extracted = 0
    errors = 0
    skipped = 0

    for code, nombre, pob in resguardos:
        if code in existing_codes:
            skipped += 1
            continue

        query = f"""RUNDEF Job
    SELECTION ALL
    UNIVERSE Personas.PA1_GRP_ETNIC=1 AND UNIDAD.UVA2_CODTER={code}
TABLE TABLE1
    AS FREQUENCY
    OF Personas.CONDICION_FISICA"""

        try:
            # POST query
            resp = requests.post(
                REDATAM_URL,
                data={
                    'MAIN': 'WebServerMain.inl',
                    'BASE': 'CNPVBASE4V2',
                    'LANG': 'esp',
                    'CODIGO': 'XXUSUARIOXX',
                    'ITEM': 'PROGRED',
                    'MODE': 'RUN',
                    'CMDSET': query,
                    'Submit': 'Ejecutar',
                },
                verify=False,
                timeout=120,
            )

            # Extract iframe URL
            match = re.search(r'src="([^"]+)"', resp.text)
            if not match:
                errors += 1
                continue

            iframe_url = match.group(1).replace('&amp;', '&')
            time.sleep(1)

            # Download result
            result = requests.get(iframe_url, verify=False, timeout=60)
            html_text = result.text

            # Parse: find Si and No values
            # Pattern: <td ...>Si</td><td ...>NUMBER</td>
            tds = re.findall(r'<td[^>]*>(.*?)</td>', html_text, re.DOTALL)
            cells = [htmlmod.unescape(re.sub(r'<[^>]+>', '', td).strip()) for td in tds]

            si_val = 0
            no_val = 0
            for i, cell in enumerate(cells):
                if cell == 'Si' and i + 1 < len(cells):
                    num = cells[i + 1].replace('\xa0', '').replace(' ', '').strip()
                    if num.isdigit():
                        si_val = int(num)
                elif cell == 'No' and i + 1 < len(cells):
                    num = cells[i + 1].replace('\xa0', '').replace(' ', '').strip()
                    if num.isdigit():
                        no_val = int(num)

            total = si_val + no_val
            tasa = round(si_val / total * 1000, 2) if total > 0 else 0

            writer.writerow([code, nombre, pob, si_val, no_val, total, tasa])
            csvfile.flush()
            extracted += 1

            if extracted % 20 == 0:
                print(f"  Extraidos: {extracted}/{len(resguardos) - skipped} | Ultimo: {nombre[:40]} si={si_val} total={total} tasa={tasa}")

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  Error en {code}: {e}")

        time.sleep(SLEEP_BETWEEN)

print(f"\n{'='*60}")
print(f"EXTRACCION COMPLETADA")
print(f"  Extraidos: {extracted}")
print(f"  Errores: {errors}")
print(f"  Saltados (ya existian): {skipped}")
print(f"  Archivo: {OUTPUT_CSV}")
print(f"{'='*60}")
