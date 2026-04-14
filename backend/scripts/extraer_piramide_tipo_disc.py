"""
Extrae piramide de capacidades diversas POR TIPO por sexo y edad para cada pueblo.
Para la tercera piramide: barras apiladas por tipo de limitacion.
Query: P_EDADR x P_SEXO WHERE PA1_GRP_ETNIC=1 AND PA11_COD_ETNIA={cod} AND CONDICION_FISICA=1 AND P_LIM_PPAL={tipo}
"""
import os, re, csv, time, sys, html as htmlmod, requests, psycopg2

sys.stdout.reconfigure(encoding='utf-8')

REDATAM_URL = "https://systema59.dane.gov.co/bincol/RpWebStats.exe/CmdSet?"
DB_URL = "postgresql://smt_admin:smt_onic_2026@localhost:5450/smt_onic"

LIMITACIONES = {
    1: 'Oir',
    2: 'Hablar',
    3: 'Ver',
    4: 'Caminar',
    5: 'Agarrar',
    6: 'Aprender',
    7: 'Autocuidado',
    8: 'Actividades diarias',
    9: 'Relacionarse',
}

AGE_ORDER = ['00-04','05-09','10-14','15-19','20-24','25-29','30-34','35-39',
             '40-44','45-49','50-54','55-59','60-64','65-69','70-74','75-79','80-84','85+']

def normalize_age(label):
    label = label.strip().lower()
    for ag in AGE_ORDER:
        nums = ag.split('-')
        if len(nums) == 2 and f"{int(nums[0]):02d}" in label and f"{int(nums[1]):02d}" in label:
            return ag
    if any(x in label for x in ['85','90','95','100']):
        return '85+'
    return None

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

# Create table
cur.execute("""
    CREATE TABLE IF NOT EXISTS pueblo.piramide_disc_tipo (
        id SERIAL PRIMARY KEY,
        periodo VARCHAR(10) DEFAULT '2018',
        cod_pueblo VARCHAR(3) NOT NULL,
        tipo_limitacion VARCHAR(30) NOT NULL,
        grupo_edad VARCHAR(20) NOT NULL,
        sexo VARCHAR(10) NOT NULL,
        valor INTEGER NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE (periodo, cod_pueblo, tipo_limitacion, grupo_edad, sexo)
    )
""")
conn.commit()

# Get pueblos - only top 30 by population (the most important for visualization)
cur.execute("""
    SELECT cod_pueblo, pueblo FROM pueblo.disc_nacional
    WHERE periodo='2018' AND COALESCE(confiabilidad,'') != 'EXCLUIR' AND total >= 200
    ORDER BY total DESC
""")
pueblos = [(r[0], r[1]) for r in cur.fetchall()]

# Check existing
cur.execute("SELECT DISTINCT cod_pueblo FROM pueblo.piramide_disc_tipo WHERE periodo='2018'")
existing = {r[0] for r in cur.fetchall()}
cur.close()
conn.close()

print(f"Pueblos a extraer: {len(pueblos)} ({len(existing)} ya extraidos)")
print(f"Tipos de limitacion: {len(LIMITACIONES)}")
print(f"Total queries: {(len(pueblos) - len(existing)) * len(LIMITACIONES)}")
print(f"Tiempo estimado: {(len(pueblos) - len(existing)) * len(LIMITACIONES) * 3 / 60:.0f} minutos")

extracted = 0
for cod, nombre in pueblos:
    if cod in existing:
        continue

    all_rows = []
    for tipo_cod, tipo_nombre in LIMITACIONES.items():
        query = f"""RUNDEF Job
    SELECTION ALL
    UNIVERSE Personas.PA1_GRP_ETNIC=1 AND Personas.PA11_COD_ETNIA={int(cod)} AND Personas.CONDICION_FISICA=1 AND Personas.P_LIM_PPAL={tipo_cod}
TABLE TABLE1
    AS CROSSTABS
    OF Personas.P_EDADR BY Personas.P_SEXO"""

        try:
            resp = requests.post(REDATAM_URL, data={
                'MAIN': 'WebServerMain.inl', 'BASE': 'CNPVBASE4V2', 'LANG': 'esp',
                'CODIGO': 'XXUSUARIOXX', 'ITEM': 'PROGRED', 'MODE': 'RUN',
                'CMDSET': query, 'Submit': 'Ejecutar',
            }, verify=False, timeout=120)

            match = re.search(r'src="([^"]+)"', resp.text)
            if not match:
                continue
            time.sleep(1)
            result = requests.get(match.group(1).replace('&amp;', '&'), verify=False, timeout=60)

            tds = re.findall(r'<td[^>]*>(.*?)</td>', result.text, re.DOTALL)
            cells = [htmlmod.unescape(re.sub(r'<[^>]+>', '', td).strip()) for td in tds]

            i = 0
            while i < len(cells):
                cell = cells[i]
                age = normalize_age(cell)
                if age and i + 2 < len(cells):
                    h = cells[i+1].replace('\xa0','').replace(' ','').strip()
                    m = cells[i+2].replace('\xa0','').replace(' ','').strip()
                    if h.isdigit() and m.isdigit():
                        all_rows.append((cod, tipo_nombre, age, 'Hombre', int(h)))
                        all_rows.append((cod, tipo_nombre, age, 'Mujer', int(m)))
                    i += 4
                else:
                    i += 1
        except:
            pass
        time.sleep(2)

    # Insert all rows for this pueblo
    if all_rows:
        conn2 = psycopg2.connect(DB_URL)
        cur2 = conn2.cursor()
        for cod_p, tipo, age, sexo, val in all_rows:
            cur2.execute("""
                INSERT INTO pueblo.piramide_disc_tipo (periodo, cod_pueblo, tipo_limitacion, grupo_edad, sexo, valor)
                VALUES ('2018', %s, %s, %s, %s, %s)
                ON CONFLICT (periodo, cod_pueblo, tipo_limitacion, grupo_edad, sexo) DO UPDATE SET valor = EXCLUDED.valor
            """, (cod_p, tipo, age, sexo, val))
        conn2.commit()
        cur2.close()
        conn2.close()
        extracted += 1
        print(f"  [{extracted}] {nombre}: {len(all_rows)} filas")

print(f"\nCompletado: {extracted} pueblos")
