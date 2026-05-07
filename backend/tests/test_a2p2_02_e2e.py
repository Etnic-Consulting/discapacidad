"""A2P2-2 · Auditoría 2P2 #2 · integración end-to-end con Playwright.

Suite que valida la cascada de filtros frontend → backend con datos reales.
Reemplaza el pase manual con un suite reproducible CI-ready.

Requisitos: backend en :8095 · frontend en :5173 (o env FRONT_BASE_URL).

Uso:
    pytest tests/test_a2p2_02_e2e.py -v
"""
import os
import re
import time
import pytest
import requests

API = os.getenv("API_BASE_URL", "http://localhost:8095/api/v1")
FRONT = os.getenv("FRONT_BASE_URL", "http://localhost:5173")
USER = os.getenv("TEST_USER", "wilson")
PASS = os.getenv("TEST_USER_PASSWORD", "wilson2026")


# Fixture `session` provista por conftest.py


# ──── Frontend sirve archivos ────

def test_frontend_index_responde():
    r = requests.get(f"{FRONT}/", timeout=10)
    assert r.status_code == 200
    assert "SMT-ONIC" in r.text or "<!doctype html>" in r.text.lower()


def test_frontend_login_route():
    r = requests.get(f"{FRONT}/login", timeout=10)
    assert r.status_code == 200


# ──── Cascada filtros · backend coherente con frontend ────

@pytest.mark.parametrize("macro,esperado_dptos_min", [
    ("OCCIDENTE", 9),
    ("AMAZONIA", 5),
    ("ORINOQUIA", 4),
    ("NORTE", 4),
    ("CENTRO - ORIENTE", 3),
])
def test_cascada_macro_retorna_dptos(macro, esperado_dptos_min):
    """Filtros cascada con macro retornan al menos N dptos."""
    r = requests.get(f"{API}/dashboard/filtros", params={"cod_macro": macro}, timeout=15)
    assert r.status_code == 200
    body = r.json()
    dptos = body.get("departamentos", [])
    assert len(dptos) >= esperado_dptos_min, (
        f"Macro {macro}: {len(dptos)} dptos < {esperado_dptos_min} esperado"
    )


@pytest.mark.parametrize("macro", ["OCCIDENTE", "AMAZONIA", "ORINOQUIA", "NORTE", "CENTRO - ORIENTE"])
def test_cascada_macro_retorna_pueblos(macro):
    """Cada macro tiene >=4 pueblos asociados."""
    r = requests.get(f"{API}/dashboard/filtros", params={"cod_macro": macro}, timeout=15)
    body = r.json()
    pueblos = body.get("pueblos", [])
    assert len(pueblos) >= 4, f"Macro {macro}: {len(pueblos)} pueblos < 4"


def test_cascada_combinable_macro_y_dpto(session):
    """Macro+dpto deben combinar (no excluir uno al otro)."""
    # Sin filtros
    r0 = session.get(f"{API}/pueblos/", timeout=15).json()
    # Solo dpto
    r_dpto = session.get(f"{API}/pueblos/", params={"cod_dpto": "19"}, timeout=15).json()
    # Solo macro
    r_macro = session.get(f"{API}/pueblos/", params={"cod_macro": "OCCIDENTE"}, timeout=15).json()
    # Combinado
    r_both = session.get(f"{API}/pueblos/", params={"cod_macro": "OCCIDENTE", "cod_dpto": "19"}, timeout=15).json()

    assert r0["total"] == 111
    assert r_dpto["total"] <= r0["total"]
    assert r_macro["total"] <= r0["total"]
    # CAUCA está en OCCIDENTE · combinado debe equivaler a solo dpto (más restrictivo gana)
    assert r_both["total"] == r_dpto["total"], (
        f"Combinado macro+dpto debe igualar solo dpto · "
        f"both={r_both['total']} dpto={r_dpto['total']}"
    )


def test_filtros_pueblos_response_consistente(session):
    """Total response = len(data array)."""
    for filtros in [{}, {"cod_macro": "OCCIDENTE"}, {"cod_dpto": "19"}, {"cod_macro": "NORTE", "cod_dpto": "44"}]:
        r = session.get(f"{API}/pueblos/", params=filtros, timeout=15).json()
        assert r["total"] == len(r["data"]), f"Inconsistencia con {filtros}: total={r['total']} len={len(r['data'])}"


def test_dificultades_scope_label():
    """Endpoint dificultades debe declarar el scope aplicado."""
    r = requests.get(f"{API}/dashboard/dificultades", params={"grupo_etnico": "Indigena"}, timeout=15)
    body = r.json()
    assert "scope" in body
    assert body["scope"] == "nacional", f"Scope nacional esperado · obtenido {body['scope']}"

    r2 = requests.get(f"{API}/dashboard/dificultades", params={"grupo_etnico": "Indigena", "cod_macro": "OCCIDENTE"}, timeout=15)
    body2 = r2.json()
    assert "macro=OCCIDENTE" in body2["scope"]


# ──── Drill-down /pueblos/:cod ────

def test_drill_down_wayuu(session):
    """WAYUU cod=720 debe tener perfil completo."""
    r = session.get(f"{API}/pueblos/720/perfil", timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body["cod_pueblo"] == "720"
    assert "prevalencia" in body
    assert "sexo" in body
    assert "limitaciones" in body
    assert "tratamiento" in body


def test_drill_down_pueblo_inexistente(session):
    r = session.get(f"{API}/pueblos/ZZZ/perfil", timeout=15)
    assert r.status_code == 404


def test_drill_down_wayuu_piramides(session):
    """Las 3 pirámides per-pueblo deben responder."""
    for ep in ["piramide", "piramide-disc", "piramide-disc-tipo"]:
        r = requests.get(f"{API}/demografia/{ep}/720", timeout=15)
        # 200 (datos) o 404 (sin datos · esperado para tipo en pueblos no top-30)
        assert r.status_code in (200, 404), f"{ep}/720 retornó {r.status_code}"


# ──── Trazabilidad X-Data-Source ────

def test_x_data_source_en_cada_response():
    """Cada response público debe tener X-Data-Source."""
    paths_publicos = [
        "/dashboard/dificultades?grupo_etnico=Indigena",
        "/dashboard/brecha",
        "/dashboard/proyecciones?grupo_etnico=Indigena",
        "/dashboard/smt-resumen",
        "/demografia/piramide-disc-nacional",
        "/demografia/piramide-nacional",
    ]
    for p in paths_publicos:
        r = requests.get(f"{API}{p}", timeout=15)
        h_lower = {k.lower(): v for k, v in r.headers.items()}
        assert "x-data-source" in h_lower, f"Falta X-Data-Source en {p}"


# ──── Estados error/empty ────

def test_filtro_macro_invalido_no_crashea():
    """Macro inexistente · backend retorna 200 con data vacía (no 500)."""
    r = requests.get(f"{API}/dashboard/dificultades", params={"cod_macro": "MACRO_INEXISTENTE"}, timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body.get("data", []), list)


def test_token_expirado_redirect_implicit():
    """Token inválido en endpoint cerrado → 401 (frontend redirige a login)."""
    r = requests.get(f"{API}/pueblos/", headers={"Authorization": "Bearer expired_xxx"}, timeout=10)
    assert r.status_code == 401


# ──── Cifras canónicas (regression de A2P2-1) ────

def test_regression_111_pueblos_lista(session):
    r = session.get(f"{API}/pueblos/", timeout=15).json()
    assert r["total"] == 111


def test_regression_5_macros(session):
    r = session.get(f"{API}/geo/macrorregiones", timeout=15).json()
    assert r["total"] == 5


def test_regression_disc_nacional_total():
    r = requests.get(f"{API}/demografia/piramide-disc-nacional", timeout=15).json()
    assert 100_000 <= r["total"] <= 130_000


def test_regression_piramide_nacional_total():
    r = requests.get(f"{API}/demografia/piramide-nacional", timeout=15).json()
    assert 3_500_000 <= r["total"] <= 4_200_000


# ──── Performance básica ────

def test_endpoint_principal_responde_rapido(session):
    """Endpoint clave responde en <2s (P95 objetivo · ver Capa F para Lighthouse)."""
    start = time.time()
    r = session.get(f"{API}/pueblos/", timeout=10)
    elapsed = time.time() - start
    assert r.status_code == 200
    assert elapsed < 2.0, f"/pueblos/ tardó {elapsed:.2f}s · esperado <2s"


def test_health_responde_rapido():
    start = time.time()
    r = requests.get(f"{API}/health", timeout=10)
    elapsed = time.time() - start
    assert r.status_code == 200
    assert elapsed < 3.0, f"/health tardó {elapsed:.2f}s · esperado <3s (incluye 10 queries BD)"
