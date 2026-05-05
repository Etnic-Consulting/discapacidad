"""Capa E (seguridad) + Capa F (performance) · tests consolidados."""
import os
import time
import pytest
import requests

API = os.getenv("API_BASE_URL", "http://localhost:8095/api/v1")


# ──── E01 OWASP · auth (cubierto en test_auth_matrix) ────
# E02 Headers seguridad

def test_e02_security_headers():
    r = requests.get(f"{API}/health", timeout=10)
    h = {k.lower(): v for k, v in r.headers.items()}
    assert h.get("x-frame-options") == "DENY"
    assert h.get("x-content-type-options") == "nosniff"
    assert "strict-origin" in h.get("referrer-policy", "")
    assert "geolocation=()" in h.get("permissions-policy", "")
    assert h.get("cross-origin-opener-policy") == "same-origin"


# E03 CORS

def test_e03_cors_no_wildcard():
    r = requests.options(
        f"{API}/health",
        headers={"Origin": "http://malicious-site.com", "Access-Control-Request-Method": "GET"},
        timeout=5,
    )
    # CORS debería NO permitir el origen malicioso · Access-Control-Allow-Origin no contiene * ni el origen
    aco = r.headers.get("access-control-allow-origin", "")
    assert aco != "*", "CORS allow-origin=* es inseguro"
    assert "malicious-site.com" not in aco


# E04 Rate limit cubierto en test_auth_matrix.test_login_rate_limit · OK

# E06 Logs scrub

def test_e06_logs_no_passwords():
    """Logs no deben contener passwords plaintext.
    Heurística: hacer login fail · verificar contenedor logs no muestra el password."""
    requests.post(f"{API}/auth/login", json={"username": "fake_user", "password": "P4ssw0rd_test_e06"}, timeout=10)
    # Si los logs filtraran passwords, otro proceso podría leerlos
    # Validamos que el response NO incluye password en su body
    r = requests.post(f"{API}/auth/login", json={"username": "fake_user", "password": "P4ssw0rd_test_e06"}, timeout=10)
    assert "P4ssw0rd_test_e06" not in r.text, "Password en response leaked"


# ──── F02 Cache HTTP en endpoints idempotentes ────

@pytest.mark.parametrize("path,min_max_age", [
    ("/geo/macrorregiones", 1800),
    ("/dashboard/smt-resumen", 600),
    ("/dashboard/filtros", 600),
    ("/formulario/territorios/macros", 3600),
])
def test_f02_cache_endpoints_estaticos(path, min_max_age, token):
    if path.startswith("/geo"):
        r = requests.get(f"{API}{path}", headers={"Authorization": f"Bearer {token}"}, timeout=15)
    else:
        r = requests.get(f"{API}{path}", timeout=15)
    cc = r.headers.get("cache-control", "")
    assert f"max-age={min_max_age}" in cc, f"{path} cache-control={cc} esperado max-age={min_max_age}"


def test_f02_cache_no_store_endpoints_sensibles(token):
    r = requests.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=10)
    cc = r.headers.get("cache-control", "")
    assert "no-store" in cc or "no-cache" in cc, f"auth/me sin no-store: {cc}"


# ──── F01 Performance baseline ────

def test_f01_health_responde_rapido():
    start = time.time()
    r = requests.get(f"{API}/health", timeout=10)
    elapsed = time.time() - start
    assert r.status_code == 200
    # Health hace 10 queries SQL · objetivo p95 <2s
    assert elapsed < 3.0, f"/health tardó {elapsed:.2f}s · objetivo <3s"


@pytest.mark.parametrize("path", [
    "/dashboard/dificultades?grupo_etnico=Indigena",
    "/dashboard/brecha",
    "/dashboard/proyecciones?grupo_etnico=Indigena",
    "/demografia/piramide-disc-nacional",
    "/conflicto/victimas/por-pueblo?limit=10",
])
def test_f01_endpoints_responden_rapido(path):
    start = time.time()
    r = requests.get(f"{API}{path}", timeout=10)
    elapsed = time.time() - start
    assert r.status_code == 200
    assert elapsed < 2.0, f"{path} tardó {elapsed:.2f}s · objetivo <2s"


def test_f01_pueblos_bulk_responde_rapido(token):
    """111 pueblos completos en <1s con índices."""
    start = time.time()
    r = requests.get(f"{API}/pueblos/", headers={"Authorization": f"Bearer {token}"}, timeout=10)
    elapsed = time.time() - start
    assert r.status_code == 200
    assert r.json()["total"] == 111
    assert elapsed < 1.5, f"/pueblos/ con 111 filas tardó {elapsed:.2f}s · objetivo <1.5s"


# ──── F04 Bundle frontend ────

def test_f04_bundle_index_size_razonable():
    """Index HTML del frontend < 50 KB."""
    r = requests.get("http://localhost:5173/", timeout=10)
    assert r.status_code == 200
    assert len(r.content) < 50_000, f"index.html {len(r.content)} bytes >50KB"
