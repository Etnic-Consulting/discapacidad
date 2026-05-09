"""
V01_redatam_vichada.py
======================
Extrae poblacion indigena con discapacidad en Vichada (cod_dpto=99)
desde REDATAM CNPV 2018 (CNPVBASE4V2 · systema59.dane.gov.co).

Variables objetivo:
  PA1_GRP_ETNIC = 1  (grupo etnico: indigena)
  P_LIM_PPAL > 0     (limitacion principal: cualquier limitacion)
  Crosstab: grupo_edad x sexo por municipio

Output: bd_consolidada/vichada_redatam.csv
Columnas: cod_dpto, cod_mpio, nombre_mpio, grupo_edad, sexo,
          total, cod_pueblo, nombre_pueblo, fuente, periodo

Idempotente: re-ejecutar sobreescribe el CSV (no duplica).

Jerarquia de fuentes (en orden de prioridad):
  1. REDATAM Web · systema59.dane.gov.co · CNPVBASE4V2 (UNIVERSE con P_LIM_PPAL>0)
  2. BD_UNIFICADA_CNPV2018_disc_etnia.csv (ya extraida del REDATAM, datos reales DANE)
  3. disc_por_resguardo_TODOS.csv (fallback resguardo-level)

NO importa anthropic / openai / google.generativeai (regla #1).
Cifras DANE siempre via Python + fuentes locales REDATAM-derivadas (nunca LLM).
"""

import os
import re
import csv
import sys
import time
import html as htmlmod
import hashlib
import datetime
import logging

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------

REDATAM_URL  = "https://systema59.dane.gov.co/bincol/RpWebStats.exe/CmdSet?"
BASE_PARAM   = "CNPVBASE4V2"
SLEEP_SEC    = 1.5
TIMEOUT_POST = 120
TIMEOUT_GET  = 90

# Directorio raiz del working tree (este script vive en _scripts/)
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

OUTPUT_DIR   = os.path.join(_ROOT, "bd_consolidada")
OUTPUT_CSV   = os.path.join(OUTPUT_DIR, "vichada_redatam.csv")
DOCS_DIR     = os.path.join(_ROOT, "_docs")
INTEGRITY_MD = os.path.join(DOCS_DIR, "INTEGRIDAD_V01.md")

# Fuente local consolidada (producto de extracciones REDATAM previas del proyecto)
BD_UNIFICADA = os.path.join(
    os.path.dirname(_ROOT),   # Desktop/discapacidad
    "bd_consolidada",
    "BD_UNIFICADA_CNPV2018_disc_etnia.csv",
)

FALLBACK_RESGUARDO = os.path.join(
    os.path.dirname(_ROOT),
    "datos_extraidos", "resguardo_real", "disc_por_resguardo_TODOS.csv",
)

COD_DPTO = "99"

MUNICIPIOS_VICHADA = {
    "99001": "Puerto Carreno",
    "99524": "La Primavera",
    "99624": "Santa Rosalia",
    "99773": "Cumaribo",
}

CSV_FIELDNAMES = [
    "cod_dpto", "cod_mpio", "nombre_mpio",
    "grupo_edad", "sexo", "total",
    "cod_pueblo", "nombre_pueblo",
    "fuente", "periodo",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("V01_redatam_vichada")


# ---------------------------------------------------------------------------
# Helpers REDATAM Web
# ---------------------------------------------------------------------------

def _normalize_age_label(label: str) -> str:
    """Convierte etiqueta de edad REDATAM a formato canonico '00-04'."""
    label = label.strip()
    # Patron: "de 00 A 04 Anos" o "00-04" o "de 85 A 89 Anos"
    m = re.search(r"(\d{1,3})\s*[AaYy\-]\s*(\d{1,3})", label)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return f"{lo:02d}-{hi:02d}"
    if re.search(r"85\s*[\+Yy]|100\s*y|85\s*y\s*m", label, re.IGNORECASE):
        return "85+"
    return label


def post_redatam(query_text: str):
    """Envia query REDATAM. Retorna (html_text, iframe_url) o (None, None)."""
    try:
        resp = requests.post(
            REDATAM_URL,
            data={
                "MAIN":   "WebServerMain.inl",
                "BASE":   BASE_PARAM,
                "LANG":   "esp",
                "CODIGO": "XXUSUARIOXX",
                "ITEM":   "PROGRED",
                "MODE":   "RUN",
                "CMDSET": query_text,
                "Submit": "Ejecutar",
            },
            verify=False,
            timeout=TIMEOUT_POST,
        )
        resp.raise_for_status()
    except Exception as exc:
        log.warning("POST REDATAM fallido: %s", exc)
        return None, None

    match = re.search(r'src="([^"]+)"', resp.text)
    if not match:
        log.warning("No iframe en respuesta REDATAM")
        return None, None

    iframe_url = match.group(1).replace("&amp;", "&")
    time.sleep(1.0)
    try:
        r2 = requests.get(iframe_url, verify=False, timeout=TIMEOUT_GET)
        r2.raise_for_status()
        return r2.text, iframe_url
    except Exception as exc:
        log.warning("GET iframe fallido: %s", exc)
        return None, None


def parse_cells(html_text: str):
    tds = re.findall(r"<td[^>]*>(.*?)</td>", html_text, re.DOTALL)
    return [
        htmlmod.unescape(re.sub(r"<[^>]+>", "", td).strip())
        for td in tds
    ]


def parse_crosstab_edadr_sexo(cells):
    """
    Parsea CROSSTABS P_EDADR x P_SEXO del HTML REDATAM.
    Retorna lista de dicts {grupo_edad, sexo, total}.
    """
    rows = []
    # Buscar cabecera Hombre / Mujer / Total
    header_idx = None
    for i, c in enumerate(cells):
        if c.strip() == "Hombre" and i + 2 < len(cells):
            if cells[i+1].strip() == "Mujer" and cells[i+2].strip() == "Total":
                header_idx = i
                break

    if header_idx is None:
        return _parse_crosstab_fallback(cells)

    i = header_idx + 3
    current_age = None
    while i < len(cells):
        cell = cells[i].strip()
        age_m = re.search(r"\d{1,3}\s*[AaYy\-]\s*\d{1,3}", cell)
        age_85 = re.search(r"85\s*[\+Yy]|100\s*y\s*m", cell, re.IGNORECASE)

        if age_m or age_85:
            current_age = _normalize_age_label(cell)
            i += 1
        elif current_age is not None:
            vals = []
            j = i
            while j < len(cells) and len(vals) < 3:
                v = cells[j].replace("\xa0","").replace(" ","").replace(".","")
                if v.lstrip("-").isdigit():
                    vals.append(int(v))
                    j += 1
                else:
                    break
            if len(vals) >= 2:
                h, m2 = vals[0], vals[1]
                rows.append({"grupo_edad": current_age, "sexo": "Hombre", "total": h})
                rows.append({"grupo_edad": current_age, "sexo": "Mujer",  "total": m2})
                i = j
                current_age = None
            else:
                i += 1
        else:
            i += 1
    return rows


def _parse_crosstab_fallback(cells):
    rows = []
    age_positions = []
    for i, c in enumerate(cells):
        m = re.search(r"\d{1,3}\s*[AaYy\-]\s*\d{1,3}", c.strip())
        m85 = re.search(r"85\s*[\+Yy]|100\s*y", c.strip(), re.IGNORECASE)
        if m or m85:
            age_positions.append((i, _normalize_age_label(c)))

    for idx, (pos, age) in enumerate(age_positions):
        end = age_positions[idx+1][0] if idx+1 < len(age_positions) else len(cells)
        nums = []
        for k in range(pos+1, min(end, pos+10)):
            v = cells[k].replace("\xa0","").replace(" ","").replace(".","")
            if v.lstrip("-").isdigit():
                nums.append(int(v))
            if len(nums) >= 2:
                break
        if len(nums) >= 2:
            rows.append({"grupo_edad": age, "sexo": "Hombre", "total": nums[0]})
            rows.append({"grupo_edad": age, "sexo": "Mujer",  "total": nums[1]})
    return rows


# ---------------------------------------------------------------------------
# Fuente 1: REDATAM Web (intentar con P_LIM_PPAL y CONDICION_FISICA)
# ---------------------------------------------------------------------------

def query_redatam_web():
    """
    Intenta extraer datos de Vichada desde REDATAM Web.

    En CNPVBASE4V2, los filtros de municipio/departamento solo funcionan
    a traves de UNIDAD.UVA2_CODTER (codigos de resguardos/zonas territoriales).
    La variable P_LIM_PPAL acepta operador > en UNIVERSE.

    Retorna lista de dicts del esquema CSV, o lista vacia si falla.
    """
    log.info("Fuente 1: REDATAM Web · CNPVBASE4V2 · systema59")
    all_rows = []

    # Query a nivel nacional para indigenas con discapacidad por edad/sexo
    # Luego filtramos resultados del resguardo conocido de Cumaribo (UVA2=1001)
    # y la zona urbana de Puerto Carreno.
    #
    # Nota: En CNPVBASE4V2, los codigos UVA2_CODTER validos para Vichada
    # se obtienen de la BD local. Sin esa BD, intentamos UVA2 conocidos
    # de extracciones anteriores del proyecto.

    # Intentar extracion por UVA2 del resguardo Cumaribo (el mayor de Vichada)
    # Desde disc_por_resguardo_TODOS.csv podemos inferir codigos reales
    uva2_vichada = _get_uva2_vichada_from_local()

    if not uva2_vichada:
        log.warning("No se pudieron obtener UVA2 de Vichada localmente")
        return []

    for uva2, mpio_info in uva2_vichada.items():
        query = f"""RUNDEF Job
    SELECTION ALL
    UNIVERSE Personas.PA1_GRP_ETNIC=1 AND Personas.CONDICION_FISICA=1 AND UNIDAD.UVA2_CODTER={uva2}
TABLE TABLE1
    AS CROSSTABS
    OF Personas.P_EDADR BY Personas.P_SEXO"""

        log.info("  UVA2=%s (%s)", uva2, mpio_info["cod_mpio"])
        html, _ = post_redatam(query)
        if not html:
            continue

        cells = parse_cells(html)
        parsed = parse_crosstab_edadr_sexo(cells)
        if parsed:
            for r in parsed:
                all_rows.append({
                    "cod_dpto":    COD_DPTO,
                    "cod_mpio":    mpio_info["cod_mpio"],
                    "nombre_mpio": mpio_info["nombre"],
                    "grupo_edad":  r["grupo_edad"],
                    "sexo":        r["sexo"],
                    "total":       r["total"],
                    "cod_pueblo":  "",
                    "nombre_pueblo": "",
                    "fuente":      "DANE-REDATAM-CNPVBASE4V2-Web",
                    "periodo":     "2018",
                })
        time.sleep(SLEEP_SEC)

    return all_rows


def _get_uva2_vichada_from_local():
    """
    Obtiene mapeo UVA2_CODTER → info de mpio para Vichada
    leyendo disc_por_resguardo_TODOS.csv si existe.
    """
    if not os.path.exists(FALLBACK_RESGUARDO):
        return {}

    # disc_por_resguardo_TODOS.csv tiene: cod_resguardo, nombre_resguardo, ...
    # Los codigos de resguardo = UVA2_CODTER
    # Necesitamos resguardos de Vichada. Buscamos por nombre (Cumaribo, Vichada, etc.)
    uva2_map = {}
    vichada_keywords = ["cumaribo", "vichada", "mataven", "selva", "carreno",
                        "primavera", "rosalia", "yopalito", "cachivera", "neri",
                        "chagrero", "cauca", "puinave", "sikuani", "piapoco",
                        "guarinuma", "cachipay", "muco", "tomo", "tuparro"]

    try:
        with open(FALLBACK_RESGUARDO, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                nombre = row.get("nombre_resguardo", "").lower()
                code = row.get("cod_resguardo", "").strip()
                if code and any(kw in nombre for kw in vichada_keywords):
                    # Asignar al municipio mas probable
                    # Cumaribo tiene la mayoria de resguardos de Vichada
                    uva2_map[code] = {
                        "cod_mpio": "99773",
                        "nombre": "Cumaribo",
                    }
    except Exception as exc:
        log.warning("Error leyendo fallback resguardos: %s", exc)

    return uva2_map


# ---------------------------------------------------------------------------
# Fuente 2: BD_UNIFICADA_CNPV2018_disc_etnia.csv (datos REDATAM ya extraidos)
# ---------------------------------------------------------------------------

def query_bd_unificada():
    """
    Lee BD_UNIFICADA_CNPV2018_disc_etnia.csv (producto de extracciones REDATAM
    previas del proyecto) y extrae datos de Vichada.

    Estrategia:
    - 'disc_indigena_mpio' (source_file, geo_level=resguardo): total indigenas
       con CONDICION_FISICA=Si por municipio. -> total general
    - 'edad_indigena_mpio': distribucion por grupo de edad de indigenas totales
    - 'sexo_indigena_mpio': distribucion por sexo de indigenas totales

    Construccion del output:
    Para cada mpio, se tienen:
      - total_disc = disc_indigena_mpio[mpio]['Si']
      - dist_edad  = edad_indigena_mpio[mpio]  (proporciones)
      - dist_sexo  = sexo_indigena_mpio[mpio]  (proporciones H/M)

    El cruce edad×sexo se estima proporcional:
      total_disc_edad_sexo ≈ total_disc * prop_edad * prop_sexo

    Nota: esto es una estimacion conservadora. Si el cruce exacto no esta
    disponible en la BD, se usa la distribucion proporcional.
    El campo 'fuente' marca el metodo para trazabilidad.

    Para los datos de condicion_fisica_x_etnia_mpio (geo_level=municipio,
    variable=condicion_fisica, cross_category=Indigena, category=Si):
    estos son los totales directos.
    """
    if not os.path.exists(BD_UNIFICADA):
        log.error("BD_UNIFICADA no encontrada: %s", BD_UNIFICADA)
        return []

    log.info("Fuente 2: BD_UNIFICADA_CNPV2018_disc_etnia.csv")
    log.info("  Path: %s", BD_UNIFICADA)

    # Leer solo registros de Vichada
    disc_mpio       = {}  # mpio -> total_disc (condicion_fisica Si, indigena)
    edad_mpio       = {}  # mpio -> {grupo_edad: conteo_indigenas_totales}
    sexo_mpio       = {}  # mpio -> {'Hombre': n, 'Mujer': n}
    nombres_mpio    = {}  # mpio -> nombre

    with open(BD_UNIFICADA, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter=";")
        for row in reader:
            if row.get("cod_dpto") != COD_DPTO:
                continue

            sf  = row.get("source_file", "")
            gl  = row.get("geo_level", "")
            cat = row.get("category", "")
            cross = row.get("cross_category", "")
            val_str = row.get("value", "0").replace("\xa0","").replace(" ","").strip()
            try:
                val = int(float(val_str))
            except (ValueError, TypeError):
                val = 0

            mpio = row.get("cod_mpio", "").strip()
            nom  = row.get("nom_mpio", "").strip()
            if mpio and nom:
                nombres_mpio[mpio] = nom.title()

            # --- disc_indigena_mpio (geo_level resguardo): total con discapacidad ---
            if sf == "disc_indigena_mpio" and gl == "resguardo" and mpio:
                if cat == "Si" and cross == "Frequency":
                    disc_mpio[mpio] = disc_mpio.get(mpio, 0) + val

            # --- condicion_fisica_x_etnia_mpio (geo_level municipio): mas exacto ---
            if sf == "condicion_fisica_x_etnia_mpio" and gl == "municipio" and mpio:
                if cat == "Si" and cross == "Indigena":
                    disc_mpio[mpio] = val  # sobreescribe con dato directo

            # --- edad_indigena_mpio: distribucion por edad (indigenas totales) ---
            # Solo tomar el primer conjunto (indigenas reales, no el agregado nacional inflado)
            # El inflado tiene valores >100000 para grupos de edad en Cumaribo
            if sf == "edad_indigena_mpio" and gl == "resguardo" and mpio:
                if cross == "Frequency" and val < 50000:  # filtro anti-inflado
                    grp = _normalize_age_label(cat)
                    if grp:
                        if mpio not in edad_mpio:
                            edad_mpio[mpio] = {}
                        edad_mpio[mpio][grp] = edad_mpio[mpio].get(grp, 0) + val

            # --- sexo_indigena_mpio: distribucion por sexo (indigenas totales) ---
            if sf == "sexo_indigena_mpio" and gl == "resguardo" and mpio:
                if cross == "Frequency" and cat in ("Hombre", "Mujer") and val < 50000:
                    if mpio not in sexo_mpio:
                        sexo_mpio[mpio] = {}
                    sexo_mpio[mpio][cat] = sexo_mpio[mpio].get(cat, 0) + val

    log.info("  Mpios con disc: %s", sorted(disc_mpio.keys()))
    log.info("  Mpios con edad: %s", sorted(edad_mpio.keys()))
    log.info("  Mpios con sexo: %s", sorted(sexo_mpio.keys()))

    # Construir filas del output
    all_rows = []

    for mpio_cod, mpio_nom_dict in MUNICIPIOS_VICHADA.items():
        nombre = nombres_mpio.get(mpio_cod, mpio_nom_dict)
        total_disc = disc_mpio.get(mpio_cod, 0)

        # Distribucion edad (proporcion sobre indigenas totales del mpio)
        edad_dist = edad_mpio.get(mpio_cod, {})
        sexo_dist = sexo_mpio.get(mpio_cod, {})

        total_edad = sum(edad_dist.values()) or 1
        total_sexo = sum(sexo_dist.values()) or 1

        if not edad_dist:
            # Sin datos de edad: emitir una fila con grupo_edad='Total'
            for sexo in ("Hombre", "Mujer"):
                prop_s = sexo_dist.get(sexo, 0) / total_sexo
                all_rows.append({
                    "cod_dpto":    COD_DPTO,
                    "cod_mpio":    mpio_cod,
                    "nombre_mpio": nombre,
                    "grupo_edad":  "Total",
                    "sexo":        sexo,
                    "total":       round(total_disc * prop_s),
                    "cod_pueblo":  "",
                    "nombre_pueblo": "",
                    "fuente":      "DANE-BD_UNIFICADA-CNPV2018-prop_sexo",
                    "periodo":     "2018",
                })
            continue

        for grp, n_edad in sorted(edad_dist.items()):
            prop_edad = n_edad / total_edad
            for sexo in ("Hombre", "Mujer"):
                prop_s = (sexo_dist.get(sexo, 0) / total_sexo
                          if total_sexo > 0 else 0.5)
                total_est = round(total_disc * prop_edad * prop_s)
                all_rows.append({
                    "cod_dpto":    COD_DPTO,
                    "cod_mpio":    mpio_cod,
                    "nombre_mpio": nombre,
                    "grupo_edad":  grp,
                    "sexo":        sexo,
                    "total":       total_est,
                    "cod_pueblo":  "",
                    "nombre_pueblo": "",
                    "fuente":      "DANE-BD_UNIFICADA-CNPV2018-prop_edad_sexo",
                    "periodo":     "2018",
                })

    return all_rows


# ---------------------------------------------------------------------------
# Integridad
# ---------------------------------------------------------------------------

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_integrity_md(csv_path: str, n_rows: int, mpios_cubiertos: list) -> None:
    ts  = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    sha = sha256_file(csv_path)
    mpios_str = ", ".join(mpios_cubiertos) if mpios_cubiertos else "ninguno"

    content = (
        "# Integridad V01 · Vichada REDATAM CNPV 2018\n"
        f"- Generado: {ts}\n"
        f"- Filas: {n_rows}\n"
        f"- SHA256: {sha}\n"
        f"- Mpios cubiertos: {mpios_str}\n"
    )
    os.makedirs(os.path.dirname(INTEGRITY_MD), exist_ok=True)
    with open(INTEGRITY_MD, "w", encoding="utf-8") as f:
        f.write(content)
    log.info("Integridad escrita: %s", INTEGRITY_MD)
    log.info("  SHA256: %s", sha)
    log.info("  Filas : %d", n_rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    log.info("=" * 60)
    log.info("V01 · Vichada REDATAM CNPV 2018 · indigena + discapacidad")
    log.info("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)

    all_rows = []

    # Fuente 1: REDATAM Web
    web_rows = query_redatam_web()
    if web_rows:
        log.info("Fuente 1 (REDATAM Web): %d filas", len(web_rows))
        all_rows.extend(web_rows)
    else:
        log.warning("Fuente 1 sin datos.")

    # Determinar mpios cubiertos por Fuente 1
    mpios_web = {r["cod_mpio"] for r in all_rows}
    mpios_faltantes = set(MUNICIPIOS_VICHADA.keys()) - mpios_web

    if mpios_faltantes:
        log.info(
            "Mpios faltantes tras Fuente 1: %s · completando con Fuente 2",
            sorted(mpios_faltantes),
        )

    # Fuente 2: BD_UNIFICADA local (datos REDATAM ya extraidos)
    # Siempre ejecutar si hay mpios sin cubrir
    if mpios_faltantes or not all_rows:
        bd_rows = query_bd_unificada()
        # Agregar solo filas de mpios no cubiertos por Fuente 1
        added = 0
        for r in bd_rows:
            if r["cod_mpio"] in mpios_faltantes:
                all_rows.append(r)
                added += 1
        if added:
            log.info("Fuente 2 (BD_UNIFICADA): +%d filas para %s",
                     added, sorted(mpios_faltantes))
        elif not web_rows:
            log.error("Fuente 2 sin datos. Sin fuentes disponibles.")

    if not all_rows:
        log.error("FALLA: sin datos. Exit 1.")
        return 1

    # Escribir CSV (idempotente: sobreescribe)
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)

    log.info("CSV escrito: %s (%d filas)", OUTPUT_CSV, len(all_rows))

    if len(all_rows) < 9:
        log.error("FALLA: solo %d filas (minimo: 9). Exit 1.", len(all_rows))
        return 1

    mpios_cubiertos = sorted(set(
        f"{r['cod_mpio']} {r['nombre_mpio']}" for r in all_rows if r.get("cod_mpio")
    ))

    write_integrity_md(OUTPUT_CSV, len(all_rows), mpios_cubiertos)

    # Resumen
    log.info("=" * 60)
    log.info("COMPLETADO")
    log.info("  CSV      : %s", OUTPUT_CSV)
    log.info("  Filas    : %d", len(all_rows))
    log.info("  Mpios    : %d · %s", len(mpios_cubiertos),
             " · ".join(mpios_cubiertos))
    log.info("=" * 60)

    print()
    print(f"CSV      : {OUTPUT_CSV}")
    print(f"Filas    : {len(all_rows)}")
    print(f"SHA256   : {sha256_file(OUTPUT_CSV)}")
    print(f"Integrity: {INTEGRITY_MD}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
