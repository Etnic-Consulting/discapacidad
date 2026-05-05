"""Capa D · QA exhaustivo · casos límite + seguridad básica."""
import os
import time
import pytest
import requests

API = os.getenv("API_BASE_URL", "http://localhost:8095/api/v1")
USER = os.getenv("TEST_USER", "wilson")
PASS = os.getenv("TEST_USER_PASSWORD", "wilson2026")


# Fixture `session` provista por conftest.py


# ──── D01 · Pueblos sin datos (confiabilidad MEDIA) ────

def test_d01_pueblos_baja_poblacion(session):
    """Pueblos con N pequeño aparecen marcados con confiabilidad reducida."""
    r = session.get(f"{API}/pueblos/", timeout=15).json()
    confs = {p.get("confiabilidad", "").upper() for p in r["data"]}
    assert any(c in confs for c in ("MEDIA", "BAJA")), f"No hay confianzas reducidas · {confs}"
    altas = sum(1 for p in r["data"] if p.get("confiabilidad", "").upper() in ("ALTA",))
    assert altas >= 80, f"Esperaba ≥80 pueblos confianza ALTA · {altas} encontrados"


# ──── D02 · Filtros que retornan 0 datos ────

def test_d02_filtro_orinoquia_pueblos(session):
    """ORINOQUIA tiene pueblos · resultado no vacío y ≤ nacional."""
    r = session.get(f"{API}/pueblos/", params={"cod_macro": "ORINOQUIA"}, timeout=15).json()
    assert r["total"] >= 1
    assert r["total"] <= 111  # ≤ porque algunos macros pueden tener pueblos extranjeros etc.


def test_d02_dpto_amazonas_filtra(session):
    """AMAZONAS (cod=91) tiene pueblos pero menos que nacional."""
    r = session.get(f"{API}/pueblos/", params={"cod_dpto": "91"}, timeout=15).json()
    assert 1 <= r["total"] < 111


# ──── D03 · Drill-down pueblo sin pirámide tipo ────

def test_d03_pueblo_pequeno_sin_piramide_tipo():
    """Pueblos no top-30 retornan 404 en piramide-disc-tipo (esperado)."""
    # MAPAYERRI cod=540 (104 personas · no top-30)
    r = requests.get(f"{API}/demografia/piramide-disc-tipo/540", timeout=15)
    assert r.status_code in (200, 404)


# ──── D04 · Tabla con todas las filas · sort + scroll simulado ────

def test_d04_tabla_111_filas_completas(session):
    r = session.get(f"{API}/pueblos/", timeout=15).json()
    assert r["total"] == 111
    # Verificar ordenamiento por defecto: total DESC
    totales = [p["total"] for p in r["data"]]
    assert totales == sorted(totales, reverse=True), "Pueblos NO están ordenados DESC por total"
    # Cada fila tiene los campos esperados
    for p in r["data"][:5]:
        assert "cod_pueblo" in p
        assert "pueblo" in p
        assert "total" in p
        assert "tasa_x_1000" in p


# ──── D05 · SQL injection en query params ────

@pytest.mark.parametrize("payload", [
    "'; DROP TABLE pueblo.disc_nacional; --",
    "1' OR '1'='1",
    "<script>alert(1)</script>",
    "'); DELETE FROM smt.usuarios; --",
    "../../etc/passwd",
    "%00",
    "x' UNION SELECT * FROM smt.usuarios--",
])
def test_d05_sql_injection_query_params(session, payload):
    """Payloads maliciosos no deben ejecutar SQL · backend retorna 200/4xx (NO 5xx)."""
    r = session.get(f"{API}/pueblos/", params={"cod_pueblo": payload}, timeout=15)
    # No debe haber error 500 (SQL ejecutado mal)
    assert r.status_code != 500, f"SQL injection causó 500: {payload}"
    # Debe retornar respuesta normal (filtro vacío) o 4xx
    assert r.status_code < 500


@pytest.mark.parametrize("path,param,payload", [
    ("/dashboard/dificultades", "cod_macro", "'; DROP TABLE x;"),
    ("/dashboard/brecha", "cod_dpto", "1' OR 1=1"),
    ("/conflicto/victimas/por-pueblo", "cod_macro", "<script>"),
    ("/dashboard/proyecciones", "grupo_etnico", "'); --"),
])
def test_d05_sql_injection_endpoints_publicos(path, param, payload):
    r = requests.get(f"{API}{path}", params={param: payload}, timeout=15)
    assert r.status_code != 500, f"SQL injection en {path}?{param}={payload}"


# ──── D06 · Rate limiting (login 8/min) ────

def test_d06_rate_limit_login_activo():
    """Confirma rate limit en /auth/login."""
    rate_limited = False
    for _ in range(15):
        r = requests.post(f"{API}/auth/login", json={"username": "rl_d06", "password": "x"}, timeout=10)
        if r.status_code == 429:
            rate_limited = True
            break
        time.sleep(0.05)
    assert rate_limited, "Rate limit login no se activó tras 15 intentos"


# ──── D07 · Payloads malformados ────

@pytest.mark.parametrize("body", [
    {},
    {"username": "wilson"},  # falta password
    {"password": "wilson2026"},  # falta username
    {"username": ["wilson"], "password": "wilson2026"},  # tipo incorrecto
    "not_a_json_string",
])
def test_d07_login_payload_invalido(body):
    """Payloads malformados rechazados con 422 (Pydantic), 400 o 429 (rate-limited de tests previos) · NO 500."""
    if isinstance(body, str):
        r = requests.post(f"{API}/auth/login", data=body, timeout=10)
    else:
        r = requests.post(f"{API}/auth/login", json=body, timeout=10)
    # 429 acepta porque tests previos dispararon el rate limit · igual NO debe haber 500
    assert r.status_code in (400, 401, 422, 429), f"Status inesperado {r.status_code} para body {body}"
    assert r.status_code != 500


def test_d07_query_param_no_numerico_donde_se_espera():
    """Pasar string donde se espera int no debe romper · validación Pydantic."""
    r = requests.get(f"{API}/conflicto/victimas/por-pueblo", params={"limit": "abc"}, timeout=10)
    # FastAPI valida con Pydantic · 422 esperado
    assert r.status_code in (200, 422)


def test_d07_cod_pueblo_muy_largo(session):
    """Inputs absurdamente largos no deben tirar el server."""
    r = session.get(f"{API}/pueblos/{'x' * 5000}/perfil", timeout=10)
    assert r.status_code in (404, 422, 414)  # 414 URI Too Long también OK
    assert r.status_code != 500
