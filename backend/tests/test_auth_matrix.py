"""B03 · Tests pytest matriz de autorización SMT-ONIC.

Valida que la matriz documentada en _docs/MATRIZ_AUTH_v1.md se cumple en runtime.

Uso:
    pytest tests/test_auth_matrix.py -v
"""
import os
import time
import pytest
import requests

BASE = os.getenv("API_BASE_URL", "http://localhost:8095/api/v1")
TEST_USER = os.getenv("TEST_USER", "wilson")
TEST_PASS = os.getenv("TEST_USER_PASSWORD", "wilson2026")


# Fixture `token` provista por conftest.py (session-scope · compartida)


# ──── Endpoints PÚBLICOS (sin token requerido) ────

@pytest.mark.parametrize("path", [
    "/health",
    "/dashboard/",
    "/dashboard/dificultades?grupo_etnico=Indigena",
    "/dashboard/brecha",
    "/dashboard/prevalencia/departamento",
    "/dashboard/smt-resumen",
    "/dashboard/intercensal?aplicar_fac=true",
    "/dashboard/proyecciones?grupo_etnico=Indigena",
    "/dashboard/panorama-kpis",
    "/dashboard/filtros",
    "/conflicto/victimas/resumen",
    "/conflicto/victimas/por-pueblo",
    "/conflicto/victimas/por-hecho",
    "/conflicto/victimas/por-tipo",
    "/demografia/piramide-nacional",
    "/demografia/piramide-disc-nacional",
    "/demografia/piramide-disc-tipo-nacional",
    "/demografia/nbi",
    "/demografia/lengua",
    "/demografia/ranking",
    "/formulario/territorios/macros",
    "/geo/macrorregiones",
    "/geo/smt/macrorregiones",
])
def test_endpoint_publico_sin_token(path):
    r = requests.get(f"{BASE}{path}", timeout=15)
    # Aceptamos 200 (datos OK) y 404 (sin datos para algunos drill-down)
    # NO debe haber 401
    assert r.status_code != 401, f"GET {path} pidió auth (no debería · es público)"
    assert r.status_code in (200, 404), f"GET {path} retornó {r.status_code}"


# ──── Endpoints AUTENTICADOS (requieren Bearer token) ────

@pytest.mark.parametrize("path", [
    "/pueblos/",
    "/pueblos/720/perfil",
    "/geo/smt/resguardos",
    "/indicadores/",
    "/indicadores/valores?periodo=2018&nivel_geo=nacional",
])
def test_endpoint_cerrado_sin_token_da_401(path):
    r = requests.get(f"{BASE}{path}", timeout=10)
    assert r.status_code == 401, f"GET {path} sin token retornó {r.status_code} (esperado 401)"


@pytest.mark.parametrize("path", [
    "/pueblos/",
    "/pueblos/720/perfil",
    "/geo/smt/resguardos",
    "/indicadores/",
])
def test_endpoint_cerrado_con_token_ok(token, path):
    r = requests.get(f"{BASE}{path}", headers={"Authorization": f"Bearer {token}"}, timeout=15)
    assert r.status_code == 200, f"GET {path} con token retornó {r.status_code} (esperado 200)"


def test_auth_me_requiere_token(token):
    r = requests.get(f"{BASE}/auth/me", timeout=10)
    assert r.status_code == 401
    r = requests.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == TEST_USER


def test_login_credenciales_invalidas():
    r = requests.post(f"{BASE}/auth/login", json={"username": "x_no_existe", "password": "wrong"}, timeout=10)
    assert r.status_code == 401


def test_token_invalido_rechazado():
    r = requests.get(
        f"{BASE}/pueblos/",
        headers={"Authorization": "Bearer fake_token_invalido_12345"},
        timeout=10,
    )
    assert r.status_code == 401


def test_logout_invalida_token():
    """Logout debe revocar el token actual · request siguiente con mismo token = 401."""
    r = requests.post(f"{BASE}/auth/login", json={"username": TEST_USER, "password": TEST_PASS}, timeout=10)
    tok = r.json()["access_token"]
    # Verificamos que funciona pre-logout
    r = requests.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {tok}"}, timeout=10)
    assert r.status_code == 200
    # Logout
    r = requests.post(f"{BASE}/auth/logout", headers={"Authorization": f"Bearer {tok}"}, timeout=10)
    assert r.status_code == 200
    # Token revocado
    time.sleep(0.5)
    r = requests.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {tok}"}, timeout=10)
    assert r.status_code == 401, "Token post-logout debería ser inválido"


def test_login_rate_limit():
    """8 intentos máximo en 60s desde misma IP."""
    # Limpiar ventana esperando o saltando · usar credenciales malas para no afectar usuario real
    fail_count = 0
    rate_limited = False
    for _ in range(15):
        r = requests.post(f"{BASE}/auth/login", json={"username": "ratelimit_test", "password": "wrong"}, timeout=10)
        if r.status_code == 429:
            rate_limited = True
            break
        elif r.status_code == 401:
            fail_count += 1
        time.sleep(0.1)
    assert rate_limited, f"Rate limit no se activó tras {fail_count} intentos · esperado tras 8"


def test_x_data_source_header_presente():
    """A09 · responses deben declarar X-Data-Source."""
    r = requests.get(f"{BASE}/dashboard/dificultades?grupo_etnico=Indigena", timeout=10)
    assert r.status_code == 200
    assert "X-Data-Source" in r.headers or "x-data-source" in r.headers, "Falta header X-Data-Source"


def test_security_headers():
    """E02 · headers de seguridad básicos presentes."""
    r = requests.get(f"{BASE}/health", timeout=10)
    headers_lower = {k.lower(): v for k, v in r.headers.items()}
    assert "x-content-type-options" in headers_lower
    assert "x-frame-options" in headers_lower
    assert headers_lower["x-frame-options"].upper() == "DENY"
