#!/usr/bin/env python3
"""W14 · Seed 200 fixtures formulario SMT con mayor diversidad.

Extiende W05 (80 fixtures) a 200 distribuidas: 40 por macro × 5 macros.
- 95% CPLI=si, 5% CPLI=no (10 rows excluidas del trigger smt.resumen)
- Variedad: 9 tipos dificultades · 5 ayudas · 3 lenguas · 5 niveles edu · 5 viviendas
- Fechas dispersas en 90 días (no 30 como W05)
- Idempotente (DELETE _fixture_w14=true antes de insert)
"""

from __future__ import annotations

import json
import os
import random
import sys
from datetime import datetime, timedelta, timezone

import psycopg2

DB_CFG = {
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": int(os.environ.get("PG_PORT", "5450")),
    "user": os.environ.get("PG_USER", "smt_admin"),
    "password": os.environ.get("PG_PASSWORD", "smt_onic_2026"),
    "dbname": os.environ.get("PG_DB", "smt_onic"),
}

MACROS = ["AMAZONIA", "NORTE", "CENTRO_ORIENTE", "OCCIDENTE", "ORINOQUIA"]
DPTOS_POR_MACRO = {
    "AMAZONIA": [("91", "AMAZONAS"), ("18", "CAQUETA"), ("95", "GUAVIARE"),
                 ("97", "VAUPES"), ("86", "PUTUMAYO")],
    "NORTE": [("08", "ATLANTICO"), ("44", "LA GUAJIRA"), ("47", "MAGDALENA"),
              ("20", "CESAR"), ("13", "BOLIVAR")],
    "CENTRO_ORIENTE": [("11", "BOGOTA"), ("25", "CUNDINAMARCA"), ("15", "BOYACA"),
                       ("68", "SANTANDER"), ("17", "CALDAS")],
    "OCCIDENTE": [("76", "VALLE"), ("19", "CAUCA"), ("05", "ANTIOQUIA"),
                  ("66", "RISARALDA"), ("52", "NARIÑO")],
    "ORINOQUIA": [("99", "VICHADA"), ("85", "CASANARE"), ("50", "META"),
                  ("81", "ARAUCA"), ("94", "GUAINIA")],
}
DIFICULTADES = ["ver", "oir", "hablar", "caminar", "agarrar", "aprender", "comer", "relacion", "tareas"]
AYUDAS = ["bastón", "silla de ruedas", "audífono", "muletas", "prótesis"]
PUEBLOS = ["282", "660", "500", "560", "800", "200", "100", "065", "720", "860"]
LENGUAS = ["si", "no", "parcial"]
EDUCACION = ["ninguno", "primaria", "secundaria", "tecnico", "universitario"]
VIVIENDA = ["bahareque", "ladrillo", "madera", "palma", "mixto"]


def _payload(macro: str, dpto: tuple[str, str], pueblo: str, idx: int) -> dict:
    return {
        "macrorregion": macro,
        "cod_dpto": dpto[0],
        "nom_dpto": dpto[1],
        "documento": f"FIXTW14_{idx:04d}",
        "edad": random.randint(15, 85),
        "sexo": random.choice(["F", "M"]),
        "cod_pueblo": pueblo,
        "lengua_materna": random.choice(LENGUAS),
        "dificultades": random.sample(DIFICULTADES, random.randint(1, 4)),
        "ayudas_tecnicas": random.sample(AYUDAS, random.randint(0, 3)),
        "salud": {
            "afiliacion": random.choice(["contributivo", "subsidiado", "no"]),
            "atencion_oportuna": random.choice(["si", "no", "parcial"]),
        },
        "educacion": {
            "asiste": random.choice(["si", "no"]),
            "nivel": random.choice(EDUCACION),
        },
        "vivienda": {
            "material_paredes": random.choice(VIVIENDA),
            "agua": random.choice(["acueducto", "rio", "pozo", "cisterna"]),
        },
        "trabajo": {
            "actividad": random.choice(["agricultura", "artesania", "ninguna", "tecnico"]),
        },
        "_fixture_w14": True,
    }


def _ensure_user(cur) -> int:
    cur.execute("SELECT id FROM smt.usuarios WHERE username = %s", ("seed_w14",))
    r = cur.fetchone()
    if r:
        return r[0]
    cur.execute(
        """
        INSERT INTO smt.usuarios (username, password_hash, salt, nombre, email, rol)
        VALUES ('seed_w14','DEBUG_NO_LOGIN','seed_salt','Seed W14 Dinamizador','seed_w14@example.local','dinamizador')
        ON CONFLICT (username) DO NOTHING
        RETURNING id
        """
    )
    r = cur.fetchone()
    if r:
        return r[0]
    cur.execute("SELECT id FROM smt.usuarios WHERE username = %s", ("seed_w14",))
    return cur.fetchone()[0]


def main() -> int:
    random.seed(42)
    total_objetivo = 200
    por_macro = total_objetivo // len(MACROS)  # 40

    conn = psycopg2.connect(**DB_CFG)
    conn.autocommit = False
    insertados_si = 0
    insertados_no = 0
    try:
        with conn.cursor() as cur:
            usuario_id = _ensure_user(cur)
            cur.execute("DELETE FROM smt.respuestas_formulario WHERE datos->>'_fixture_w14' = 'true'")
            ahora = datetime.now(tz=timezone.utc)
            idx = 0
            for macro in MACROS:
                dptos = DPTOS_POR_MACRO[macro]
                for _ in range(por_macro):
                    dpto = random.choice(dptos)
                    pueblo = random.choice(PUEBLOS)
                    payload = _payload(macro, dpto, pueblo, idx)
                    fecha = ahora - timedelta(
                        days=random.randint(0, 89),
                        hours=random.randint(0, 23),
                    )
                    cpli = "si" if random.random() < 0.95 else "no"
                    cur.execute(
                        """
                        INSERT INTO smt.respuestas_formulario
                            (usuario_id, cod_pueblo, cod_dpto, cod_mpio,
                             nombre_comunidad, fecha_envio, datos, cpli_consentimiento)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            usuario_id, pueblo, dpto[0],
                            f"{dpto[0]}{random.randint(100,999):03d}",
                            f"Comunidad {idx}", fecha, json.dumps(payload), cpli,
                        ),
                    )
                    if cpli == "si":
                        insertados_si += 1
                    else:
                        insertados_no += 1
                    idx += 1
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"ERR: {e}", file=sys.stderr)
        return 2
    finally:
        conn.close()

    print(f"W14 · {insertados_si + insertados_no} fixtures insertadas ({insertados_si} cpli=si · {insertados_no} cpli=no)")

    conn = psycopg2.connect(**DB_CFG)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM smt.respuestas_formulario "
                "WHERE datos->>'_fixture_w14' = 'true' AND cpli_consentimiento = 'si'"
            )
            n_si = cur.fetchone()[0]
            cur.execute("SELECT dimension, COUNT(*) FROM smt.resumen GROUP BY dimension")
            dims = {r[0]: r[1] for r in cur.fetchall()}
        print(f"  · _fixture_w14 cpli=si: {n_si}")
        print(f"  · smt.resumen dimensions: {dims}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
