"""
Extrae piramide de capacidades diversas por sexo y edad quinquenal para cada pueblo.
Query: P_EDADR × P_SEXO WHERE PA1_GRP_ETNIC=1 AND PA11_COD_ETNIA={cod} AND CONDICION_FISICA=1
"""
import os, re, csv, time, sys, html as htmlmod, requests, psycopg2

sys.stdout.reconfigure(encoding='utf-8')

REDATAM_URL = "https://systema59.dane.gov.co/bincol/RpWebStats.exe/CmdSet?"
OUTPUT_CSV = "C:/Users/wilso/Desktop/discapacidad/datos_extraidos/pueblo_x_mpio/piramide_disc_x_pueblo.csv"
DB_URL = "postgresql://smt_admin:smt_onic_2026@localhost:5450/smt_onic"

# Get pueblo codes
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()
cur.execute("SELECT cod_pueblo, pueblo FROM pueblo.disc_nacional WHERE periodo='2018' AND COALESCE(confiabilidad,'') != 'EXCLUIR' ORDER BY total DESC")
pueblos = [(r[0], r[1]) for r in cur.fetchall()]

# Create table
cur.execute("""
    CREATE TABLE IF NOT EXISTS pueblo.piramide_disc (
        id SERIAL PRIMARY KEY,
        periodo VARCHAR(10) DEFAULT '2018',
        cod_pueblo VARCHAR(3) NOT NULL,
        pueblo VARCHAR(100),
        grupo_edad VARCHAR(20) NOT NULL,
        sexo VARCHAR(10) NOT NULL,
        valor INTEGER NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE (periodo, cod_pueblo, grupo_edad, sexo)
    )
""")
conn.commit()

# Check what we already have
cur.execute("SELECT DISTINCT cod_pueblo FROM pueblo.piramide_disc WHERE periodo='2018'")
existing = {r[0] for r in cur.fetchall()}
cur.close()
conn.close()

print(f"Pueblos a extraer: {len(pueblos)} ({len(existing)} ya extraidos)")

AGE_ORDER = ['00-04','05-09','10-14','15-19','20-24','25-29','30-34','35-39',
             '40-44','45-49','50-54','55-59','60-64','65-69','70-74','75-79','80-84','85+']

def normalize_age(label):
    label = label.strip().lower()
    for ag in AGE_ORDER:
        nums = ag.split('-')
        if len(nums) == 2 and f"{int(nums[0]):02d}" in label and f"{int(nums[1]):02d}" in label:
            return ag
    if '85' in label or '90' in label or '95' in label or '100' in label:
        return '85+'
    return label

extracted = 0
for cod, nombre in pueblos:
    if cod in existing:
        continue

    query = f"""RUNDEF Job
    SELECTION ALL
    UNIVERSE Personas.PA1_GRP_ETNIC=1 AND Personas.PA11_COD_ETNIA={int(cod)} AND Personas.CONDICION_FISICA=1
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
        iframe_url = match.group(1).replace('&amp;', '&')
        time.sleep(1)
        result = requests.get(iframe_url, verify=False, timeout=60)

        tds = re.findall(r'<td[^>]*>(.*?)</td>', result.text, re.DOTALL)
        cells = [htmlmod.unescape(re.sub(r'<[^>]+>', '', td).strip()) for td in tds]

        # Parse: age group rows with Hombre, Mujer, Total columns
        rows = []
        i = 0
        while i < len(cells):
            cell = cells[i]
            if 'A' in cell and ('0' in cell or '5' in cell) and 'os' in cell.lower():
                age = normalize_age(cell)
                if i + 2 < len(cells):
                    h = cells[i+1].replace('\xa0','').replace(' ','').strip()
                    m = cells[i+2].replace('\xa0','').replace(' ','').strip()
                    if h.isdigit() and m.isdigit():
                        rows.append((age, 'Hombre', int(h)))
                        rows.append((age, 'Mujer', int(m)))
                i += 4
            else:
                i += 1

        # Merge 85+ groups
        merged = {}
        for age, sexo, val in rows:
            key = (age if age != '85+' else '85+', sexo)
            merged[key] = merged.get(key, 0) + val

        if merged:
            conn2 = psycopg2.connect(DB_URL)
            cur2 = conn2.cursor()
            for (age, sexo), val in merged.items():
                cur2.execute("""
                    INSERT INTO pueblo.piramide_disc (periodo, cod_pueblo, pueblo, grupo_edad, sexo, valor)
                    VALUES ('2018', %s, %s, %s, %s, %s)
                    ON CONFLICT (periodo, cod_pueblo, grupo_edad, sexo) DO UPDATE SET valor = EXCLUDED.valor
                """, (cod, nombre, age, sexo, val))
            conn2.commit()
            cur2.close()
            conn2.close()
            extracted += 1
            if extracted % 10 == 0:
                print(f"  Extraidos: {extracted} | Ultimo: {nombre}")

    except Exception as e:
        if extracted < 3:
            print(f"  Error {cod}: {e}")

    time.sleep(2)

print(f"\nCompletado: {extracted} pueblos con piramide de cap. diversas")
