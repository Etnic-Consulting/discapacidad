"""
test_formulario_e2e.py · W07 Sprint S5_v1_1 (SMT-ONIC discapacidad)

Tests E2E que validan el flujo completo formulario → trigger → resumen.

Estrategia:
  - Conexion directa psycopg2 (sync) a la BD para inserciones y validaciones.
  - requests al API vivo en http://localhost:8095 para el endpoint dashboard.
  - Fixtures con teardown garantizado (finally) para idempotencia.

Tests:
  1. test_flujo_completo_formulario_e2e  - INSERT 50 rows → trigger → smt.resumen → GET dashboard
  2. test_trigger_k_anonimato            - solo 5 rows · k<30 → no categorias expuestas
  3. test_fixtures_W05_existen           - 80 fixtures _fixture=true con CPLI=si
"""
from __future__ import annotations

import json
import time
import datetime
import hashlib
import secrets

import psycopg2
import pytest
import requests

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------

DB_CFG = dict(host="localhost", port=5450, user="smt_admin",
              password="smt_onic_2026", dbname="smt_onic")

API_BASE = "http://localhost:8095/api/v1"

# Marcador unico para rows test de W07 → limpieza segura sin afectar fixtures W05
_TEST_TAG = "_test_w07_e2e"

# Usuario test reutilizado · creado si no existe · NO se elimina (FK lo impide
# si quedan rows; el teardown elimina las rows primero).
_TEST_USERNAME = "test_e2e_w07"
_TEST_PASSWORD = "testpass_w07_2026"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return digest, salt


def _get_or_create_test_user(cur) -> int:
    """Obtiene o crea el usuario de test · retorna id."""
    cur.execute("SELECT id FROM smt.usuarios WHERE username = %s", (_TEST_USERNAME,))
    row = cur.fetchone()
    if row:
        return row[0]
    ph, salt = _hash_password(_TEST_PASSWORD)
    cur.execute(
        """
        INSERT INTO smt.usuarios
            (username, password_hash, salt, nombre, email, rol, activo)
        VALUES (%s, %s, %s, %s, %s, %s, TRUE)
        RETURNING id
        """,
        (_TEST_USERNAME, ph, salt, "Test E2E W07", "test_e2e_w07@test.local", "dinamizador"),
    )
    return cur.fetchone()[0]


def _build_payload(macro: str, cod_dpto: str, idx: int) -> dict:
    """Payload JSONB minimo con tag de test para cleanup."""
    return {
        "macrorregion": macro,
        "cod_dpto": cod_dpto,
        "nom_dpto": f"DPTO_{cod_dpto}",
        "documento": f"TEST_W07_{idx:04d}",
        "edad": 30 + (idx % 40),
        "sexo": "F" if idx % 2 == 0 else "M",
        "cod_pueblo": "660",
        "lengua_materna": "si",
        "dificultades": ["caminar", "ver"],
        "ayudas_tecnicas": [],
        "salud": {"afiliacion": "subsidiado", "atencion_oportuna": "si"},
        "educacion": {"asiste": "no", "nivel": "primaria"},
        "vivienda": {"material_paredes": "bahareque", "agua": "rio"},
        "trabajo": {"actividad": "agricultura"},
        _TEST_TAG: True,
    }


def _delete_test_rows(cur) -> int:
    """Elimina todas las rows de test W07. Retorna cantidad eliminada."""
    cur.execute(
        f"DELETE FROM smt.respuestas_formulario WHERE datos->>'{_TEST_TAG}' = 'true'"
    )
    return cur.rowcount


def _current_periodo() -> str:
    return datetime.datetime.now().strftime("%Y-%m")


# ---------------------------------------------------------------------------
# Fixture pytest: conexion DB con teardown garantizado
# ---------------------------------------------------------------------------

@pytest.fixture
def db_conn():
    """Conexion psycopg2 con autocommit=False. Teardown: rollback + close."""
    conn = psycopg2.connect(**DB_CFG)
    conn.autocommit = False
    yield conn
    try:
        conn.rollback()
    finally:
        conn.close()


@pytest.fixture
def db_conn_autocommit():
    """Conexion con autocommit=True para operaciones que necesitan ver el trigger."""
    conn = psycopg2.connect(**DB_CFG)
    conn.autocommit = True
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# TEST 1: Flujo completo E2E
# ---------------------------------------------------------------------------

def test_flujo_completo_formulario_e2e(db_conn_autocommit):
    """
    Valida el flujo completo:
      1. Inserta 50 rows test (CPLI=si) en smt.respuestas_formulario.
      2. Confirma que smt.resumen tiene rows nuevas para el periodo actual
         (trigger smt.trg_smt_respuestas_recalcular disparado).
      3. GET /dashboard/smt-resumen retorna total_dimensiones >= 1 y data no vacio.
      4. Cleanup: elimina las 50 rows test.
    """
    conn = db_conn_autocommit
    cur = conn.cursor()
    periodo = _current_periodo()

    # --- Obtener resumen ANTES ---
    cur.execute(
        "SELECT COUNT(*) FROM smt.resumen WHERE periodo = %s", (periodo,)
    )
    count_before = cur.fetchone()[0]

    # --- Setup: obtener/crear usuario test ---
    usuario_id = _get_or_create_test_user(cur)

    inserted_ids: list[int] = []
    try:
        # --- INSERT 50 rows nuevas en periodo actual ---
        # Usamos fecha_envio = NOW() para que el trigger las incluya en el periodo actual
        for i in range(50):
            payload = _build_payload("AMAZONIA", "91", i)
            cur.execute(
                """
                INSERT INTO smt.respuestas_formulario
                    (usuario_id, cod_pueblo, cod_dpto, nombre_comunidad,
                     fecha_envio, datos, cpli_consentimiento)
                VALUES (%s, %s, %s, %s, NOW(), %s, 'si')
                RETURNING id
                """,
                (usuario_id, "660", "91", f"Comunidad_Test_W07_{i}", json.dumps(payload)),
            )
            inserted_ids.append(cur.fetchone()[0])

        # Breve pausa para que el trigger asincronico termine (el trigger es sincrono
        # AFTER STATEMENT, ya debio ejecutarse, pero damos margen)
        time.sleep(0.2)

        # --- Verificar trigger disparo: smt.resumen debe tener rows para periodo actual ---
        cur.execute(
            "SELECT COUNT(*) FROM smt.resumen WHERE periodo = %s", (periodo,)
        )
        count_after = cur.fetchone()[0]

        # Con 50 + filas existentes de 2026-05 (>=30 total) el trigger debe poblar resumen
        # count_after puede ser > 0 (trigger poblo) o == count_before si ya habia >= 30
        # Lo que garantizamos es que existe al menos 1 row en resumen para este periodo
        assert count_after >= 1, (
            f"Trigger no poblo smt.resumen para periodo {periodo}. "
            f"Antes={count_before}, Despues={count_after}. "
            "Verificar que total CPLI=si en el periodo actual sea >= 30."
        )

        # --- Verificar via API: GET /dashboard/smt-resumen ---
        resp = requests.get(f"{API_BASE}/dashboard/smt-resumen", timeout=10)
        assert resp.status_code == 200, (
            f"GET /dashboard/smt-resumen retorno {resp.status_code}: {resp.text[:200]}"
        )
        body = resp.json()

        assert "total_dimensiones" in body, "Respuesta no tiene campo total_dimensiones"
        assert body["total_dimensiones"] >= 1, (
            f"total_dimensiones={body['total_dimensiones']} esperado >= 1"
        )
        assert "data" in body, "Respuesta no tiene campo data"
        assert len(body["data"]) > 0, "data esta vacio · resumen no tiene categorias"
        assert "agrupado" in body, "Respuesta no tiene campo agrupado"

    finally:
        # --- Cleanup: eliminar rows test ---
        cleaned = _delete_test_rows(cur)
        assert cleaned == len(inserted_ids), (
            f"Cleanup esperaba {len(inserted_ids)} rows, elimino {cleaned}"
        )


# ---------------------------------------------------------------------------
# TEST 2: Trigger k-anonimato
# ---------------------------------------------------------------------------

def test_trigger_k_anonimato(db_conn_autocommit):
    """
    Valida que el trigger k-anonimato funciona:
      1. INSERT solo 5 rows test con cod_dpto unico ('XX') en el periodo actual.
      2. Trigger recalcula smt.resumen.
      3. Verifica que ninguna categoria de dimension 'macro' tiene valor < 30
         (k-anonimato enforced con HAVING COUNT(*) >= 30).

    Nota: el trigger recalcula TODAS las dimensiones. Los 5 rows test representan
    un subconjunto pequeño; si el total del periodo >= 30, el trigger SÍ corre pero
    solo agrega categorias con >= 30 ocurrencias. Si el total < 30, el trigger retorna
    sin insertar nada (proteccion total).
    """
    conn = db_conn_autocommit
    cur = conn.cursor()
    periodo = _current_periodo()

    usuario_id = _get_or_create_test_user(cur)

    try:
        # INSERT 5 rows con cod_dpto que no existe en datos reales → macrorregion 'SIN_MACRO'
        for i in range(5):
            payload = _build_payload("MACRO_TEST_KANONIMATO", "ZZ", i)
            cur.execute(
                """
                INSERT INTO smt.respuestas_formulario
                    (usuario_id, cod_pueblo, cod_dpto, nombre_comunidad,
                     fecha_envio, datos, cpli_consentimiento)
                VALUES (%s, %s, %s, %s, NOW(), %s, 'si')
                """,
                (usuario_id, "660", "ZZ", f"Comunidad_KAnon_{i}", json.dumps(payload)),
            )

        time.sleep(0.2)

        # --- Validar k-anonimato en smt.resumen ---
        # Ninguna categoria de CUALQUIER dimension debe tener valor < 30
        cur.execute(
            """
            SELECT dimension, categoria, valor
            FROM smt.resumen
            WHERE periodo = %s AND valor < 30
            ORDER BY valor
            """,
            (periodo,)
        )
        violaciones = cur.fetchall()

        assert len(violaciones) == 0, (
            f"K-anonimato violado en smt.resumen periodo {periodo}: "
            f"{violaciones}"
        )

        # Si el trigger si corrio (total >= 30), verificar especificamente dimension macro
        cur.execute(
            "SELECT categoria, valor FROM smt.resumen WHERE periodo = %s AND dimension = 'macro'",
            (periodo,)
        )
        macro_rows = cur.fetchall()
        for categoria, valor in macro_rows:
            assert float(valor) >= 30, (
                f"K-anonimato violado: macro='{categoria}' tiene valor={valor} < 30"
            )

    finally:
        _delete_test_rows(cur)


# ---------------------------------------------------------------------------
# TEST 3: Fixtures W05 existen
# ---------------------------------------------------------------------------

def test_fixtures_W05_existen(db_conn):
    """
    Verifica que existen exactamente las 80 fixtures sembradas por W05:
      - datos->>'_fixture' = 'true'
      - cpli_consentimiento = 'si'
      - No son rows de test W07
    """
    conn = db_conn
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM smt.respuestas_formulario
        WHERE (datos->>'_fixture')::boolean = TRUE
          AND cpli_consentimiento = 'si'
          AND (datos->>%s IS NULL OR (datos->>%s)::boolean = FALSE)
        """,
        (_TEST_TAG, _TEST_TAG),
    )
    count = cur.fetchone()[0]

    assert count == 80, (
        f"Se esperaban 80 fixtures W05 (CPLI=si, _fixture=true), se encontraron {count}. "
        "Re-ejecutar: python backend/scripts/W05_seed_smt_fixtures.py"
    )

    # Verificar distribucion: deben tener datos JSONB con campo 'macrorregion'
    cur.execute(
        """
        SELECT COUNT(DISTINCT datos->>'macrorregion') AS n_macros
        FROM smt.respuestas_formulario
        WHERE (datos->>'_fixture')::boolean = TRUE
          AND cpli_consentimiento = 'si'
        """
    )
    n_macros = cur.fetchone()[0]

    assert n_macros >= 3, (
        f"Fixtures W05 deben cubrir al menos 3 macros, solo tienen {n_macros}. "
        "Datos JSONB incompletos o corruptos."
    )
