#!/usr/bin/env python3
"""W05 · Seed 80 fixtures smt.respuestas_formulario distribuidas en 5 macros.

Inserta 80 respuestas con CPLI=si, datos JSONB completos, fechas dispersas
en los ultimos 30 dias. Distribucion: 16 por macro (AMAZONIA, NORTE, CENTRO_ORIENTE,
OCCIDENTE, ORINOQUIA). Garantiza que el trigger smt.recalcular_resumen() pueda
generar agregaciones >= 30 por dimension.
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
    "port": int(os.environ.get("PG_PORT", "5432")),
    "user": os.environ.get("PG_USER", "smt_admin"),
    "password": os.environ.get("PG_PASSWORD", "smt_onic_2026"),
    "dbname": os.environ.get("PG_DB", "smt_onic"),
}

MACROS = ["AMAZONIA", "NORTE", "CENTRO_ORIENTE", "OCCIDENTE", "ORINOQUIA"]
DPTOS_POR_MACRO = {
    "AMAZONIA": [("91", "AMAZONAS"), ("18", "CAQUETA"), ("95", "GUAVIARE")],
    "NORTE": [("08", "ATLANTICO"), ("44", "LA GUAJIRA"), ("47", "MAGDALENA"), ("20", "CESAR")],
    "CENTRO_ORIENTE": [("11", "BOGOTA"), ("25", "CUNDINAMARCA"), ("15", "BOYACA")],
    "OCCIDENTE": [("76", "VALLE DEL CAUCA"), ("19", "CAUCA"), ("05", "ANTIOQUIA"), ("66", "RISARALDA")],
    "ORINOQUIA": [("99", "VICHADA"), ("85", "CASANARE"), ("50", "META"), ("81", "ARAUCA")],
}
DIFICULTADES = [
    "ver", "oir", "hablar", "caminar", "agarrar",
    "aprender", "comer", "relacion", "tareas",
]
PUEBLOS = ["282", "660", "500", "560", "800", "200", "100", "065"]


def _insertar_usuario_test(cur) -> int:
    """Asegura usuario test 'seed_dinamizador' existe · retorna id."""
    cur.execute(
        "SELECT id FROM smt.usuarios WHERE username = %s",
        ("seed_dinamizador",),
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        """
        INSERT INTO smt.usuarios (username, password_hash, salt, nombre, email, rol)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            "seed_dinamizador",
            "DEBUG_NO_LOGIN",  # hash no usable · solo para FK
            "seed_salt",
            "Seed Dinamizador (W05 fixtures)",
            "seed@example.local",
            "dinamizador",
        ),
    )
    return cur.fetchone()[0]


def _generar_payload(macro: str, dpto: tuple[str, str], pueblo: str, idx: int) -> dict:
    """Genera datos JSONB completos · cumple shape esperado por dashboard."""
    edad = random.randint(20, 75)
    sexo = random.choice(["F", "M"])
    n_dificultades = random.randint(1, 4)
    dificultades = random.sample(DIFICULTADES, n_dificultades)
    return {
        "macrorregion": macro,
        "cod_dpto": dpto[0],
        "nom_dpto": dpto[1],
        "documento": f"FIXT{1000 + idx}",
        "edad": edad,
        "sexo": sexo,
        "cod_pueblo": pueblo,
        "lengua_materna": random.choice(["si", "no", "parcial"]),
        "dificultades": dificultades,
        "ayudas_tecnicas": random.choice([[], ["bastón"], ["silla"], ["audífono"]]),
        "salud": {
            "afiliacion": random.choice(["contributivo", "subsidiado", "no"]),
            "atencion_oportuna": random.choice(["si", "no"]),
        },
        "educacion": {
            "asiste": random.choice(["si", "no"]),
            "nivel": random.choice(["ninguno", "primaria", "secundaria"]),
        },
        "vivienda": {
            "material_paredes": random.choice(["bahareque", "ladrillo", "madera"]),
            "agua": random.choice(["acueducto", "rio", "pozo"]),
        },
        "trabajo": {
            "actividad": random.choice(["agricultura", "artesania", "ninguna"]),
        },
        "_fixture": True,
    }


def main() -> int:
    random.seed(42)
    total_objetivo = 80
    por_macro = total_objetivo // len(MACROS)  # 16

    conn = psycopg2.connect(**DB_CFG)
    conn.autocommit = False
    insertados = 0
    try:
        with conn.cursor() as cur:
            usuario_id = _insertar_usuario_test(cur)

            # Limpiar fixtures anteriores (idempotencia)
            cur.execute(
                "DELETE FROM smt.respuestas_formulario WHERE datos->>'_fixture' = 'true'"
            )

            ahora = datetime.now(tz=timezone.utc)
            idx = 0
            for macro in MACROS:
                dptos = DPTOS_POR_MACRO[macro]
                for _ in range(por_macro):
                    dpto = random.choice(dptos)
                    pueblo = random.choice(PUEBLOS)
                    payload = _generar_payload(macro, dpto, pueblo, idx)
                    fecha = ahora - timedelta(days=random.randint(0, 29), hours=random.randint(0, 23))
                    cur.execute(
                        """
                        INSERT INTO smt.respuestas_formulario
                            (usuario_id, cod_pueblo, cod_dpto, cod_mpio,
                             nombre_comunidad, fecha_envio, datos, cpli_consentimiento)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            usuario_id,
                            pueblo,
                            dpto[0],
                            f"{dpto[0]}{random.randint(100, 999):03d}",
                            f"Comunidad {idx}",
                            fecha,
                            json.dumps(payload),
                            "si",
                        ),
                    )
                    insertados += 1
                    idx += 1
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"ERR: {e}", file=sys.stderr)
        return 2
    finally:
        conn.close()

    print(f"W05 · {insertados} fixtures insertadas en smt.respuestas_formulario.")

    # Verificar · trigger debe haber poblado smt.resumen
    conn = psycopg2.connect(**DB_CFG)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM smt.respuestas_formulario "
                "WHERE datos->>'_fixture' = 'true' AND cpli_consentimiento = 'si'"
            )
            n_fix = cur.fetchone()[0]
            cur.execute("SELECT dimension, COUNT(*) FROM smt.resumen GROUP BY dimension")
            dim_counts = {r[0]: r[1] for r in cur.fetchall()}
        print(f"  · respuestas_formulario fixtures CPLI=si: {n_fix}")
        print(f"  · smt.resumen dimensions: {dim_counts}")
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
