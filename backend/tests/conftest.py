"""Conftest común · token compartido entre archivos de test (evita rate limit)."""
import os
import time
import pytest
import requests

API = os.getenv("API_BASE_URL", "http://localhost:8095/api/v1")
USER = os.getenv("TEST_USER", "wilson")
PASS = os.getenv("TEST_USER_PASSWORD", "wilson2026")

_token_cache = {"token": None, "obtained_at": 0}


@pytest.fixture(scope="session")
def token():
    """Token obtenido UNA VEZ por session pytest · compartido por todos los tests."""
    if _token_cache["token"] and time.time() - _token_cache["obtained_at"] < 3600:
        return _token_cache["token"]
    # Reintenta con backoff si rate-limited
    for _ in range(3):
        r = requests.post(f"{API}/auth/login", json={"username": USER, "password": PASS}, timeout=10)
        if r.status_code == 200:
            tk = r.json()["access_token"]
            _token_cache["token"] = tk
            _token_cache["obtained_at"] = time.time()
            return tk
        if r.status_code == 429:
            time.sleep(20)
    raise RuntimeError(f"No se pudo login tras 3 intentos · status={r.status_code}")


@pytest.fixture(scope="session")
def session(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s
