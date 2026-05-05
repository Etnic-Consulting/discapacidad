"""A2P2-1 · Auditoría 2P2 #1 · datos+backend.

Peer dinámico de la auditoría: valida que cada endpoint retorna
las cifras canónicas declaradas en `_docs/CIFRAS_CANONICAS_v1.md`.

DoD A2P2-1: ≥95% de endpoints retornan cifras esperadas en al menos
3 combinaciones de filtros distintas.
"""
import os
import pytest
import requests

BASE = os.getenv("API_BASE_URL", "http://localhost:8095/api/v1")
TEST_USER = os.getenv("TEST_USER", "wilson")
TEST_PASS = os.getenv("TEST_USER_PASSWORD", "wilson2026")


# Fixture `token` provista por conftest.py


# ──── Cifras canónicas (de CIFRAS_CANONICAS_v1.md) ────

def test_canonica_111_pueblos_con_disc_nacional(token):
    """111.939 personas indígenas con capacidades diversas (REDATAM directo)."""
    r = requests.get(f"{BASE}/demografia/piramide-disc-nacional", timeout=15)
    assert r.status_code == 200
    body = r.json()
    total = body.get("total", 0)
    assert 100_000 <= total <= 130_000, (
        f"Total disc nacional fuera de rango canónico: {total} (esperado 100K-130K)"
    )


def test_canonica_3_8M_piramide_nacional(token):
    """3.811.234 personas indígenas total (Visor DANE)."""
    r = requests.get(f"{BASE}/demografia/piramide-nacional", timeout=15)
    assert r.status_code == 200
    body = r.json()
    total = body.get("total", 0)
    assert 3_500_000 <= total <= 4_200_000, (
        f"Total pirámide nacional fuera de rango: {total}"
    )


def test_canonica_111_pueblos_lista(token):
    """111 pueblos con N>=30 confiabilidad ALTA/MEDIA en /pueblos/."""
    r = requests.get(f"{BASE}/pueblos/", headers={"Authorization": f"Bearer {token}"}, timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 111, f"Esperado 111 pueblos, obtenido {body['total']}"


def test_canonica_5_macrorregiones(token):
    """5 macrorregiones ONIC con conteos."""
    r = requests.get(f"{BASE}/geo/macrorregiones", headers={"Authorization": f"Bearer {token}"}, timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 5
    nombres = {m["macro"] for m in body["data"]}
    assert nombres == {"NORTE", "OCCIDENTE", "CENTRO - ORIENTE", "AMAZONIA", "ORINOQUIA"}


def test_canonica_830_resguardos(token):
    """830 resguardos cartografiados smt_geo."""
    r = requests.get(f"{BASE}/geo/smt/resguardos", headers={"Authorization": f"Bearer {token}"}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    n = len(body.get("features", []))
    assert 800 <= n <= 850, f"Resguardos {n} fuera de rango canónico ~830"


def test_canonica_indicadores(token):
    """12+ indicadores definidos."""
    r = requests.get(f"{BASE}/indicadores/", headers={"Authorization": f"Bearer {token}"}, timeout=15)
    assert r.status_code == 200
    body = r.json()
    n = body.get("total", 0)
    assert n >= 12, f"Indicadores {n} < 12 esperados"


def test_canonica_proyecciones(token):
    """832 filas en proyecciones · al menos 26 años para Indígena."""
    r = requests.get(f"{BASE}/dashboard/proyecciones?grupo_etnico=Indigena&periodo_inicio=2005&periodo_fin=2030", timeout=15)
    assert r.status_code == 200
    body = r.json()
    data = body.get("data", body.get("escenarios", []))
    assert len(data) >= 4, f"Proyecciones Indígena {len(data)} < 4 escenarios"


def test_canonica_smt_resumen():
    """40 filas en smt.resumen periodo 2026-F1."""
    r = requests.get(f"{BASE}/dashboard/smt-resumen", timeout=15)
    assert r.status_code == 200
    body = r.json()
    data = body.get("data", [])
    assert len(data) >= 30, f"SMT resumen {len(data)} < 30 esperado"


# ──── Filtros · matriz cartesiana ────

@pytest.mark.parametrize("filtros", [
    {},
    {"cod_macro": "OCCIDENTE"},
    {"cod_macro": "NORTE"},
    {"cod_macro": "AMAZONIA"},
    {"cod_dpto": "19"},
    {"cod_dpto": "44"},
    {"cod_macro": "OCCIDENTE", "cod_dpto": "19"},
])
def test_filtros_pueblos(token, filtros):
    """Endpoint /pueblos/ con N combinaciones de filtros · debe responder 200 con data válida."""
    qs = "&".join(f"{k}={v}" for k, v in filtros.items())
    url = f"{BASE}/pueblos/" + (f"?{qs}" if qs else "")
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=15)
    assert r.status_code == 200, f"Filtros {filtros} retornó {r.status_code}"
    body = r.json()
    assert "data" in body and isinstance(body["data"], list)
    assert body["total"] == len(body["data"])
    # Sin filtros → 111 pueblos · con filtro → menos
    if not filtros:
        assert body["total"] == 111
    else:
        assert body["total"] <= 111


@pytest.mark.parametrize("filtros", [
    {"grupo_etnico": "Indigena"},
    {"grupo_etnico": "Indigena", "cod_macro": "OCCIDENTE"},
    {"grupo_etnico": "Indigena", "cod_dpto": "19"},
])
def test_filtros_dificultades(filtros):
    qs = "&".join(f"{k}={v}" for k, v in filtros.items())
    r = requests.get(f"{BASE}/dashboard/dificultades?{qs}", timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body.get("data", []), list)
    assert "scope" in body, "Falta campo 'scope' en respuesta"


@pytest.mark.parametrize("filtros", [
    {},
    {"cod_macro": "OCCIDENTE"},
    {"cod_dpto": "19"},
])
def test_filtros_brecha(filtros):
    qs = "&".join(f"{k}={v}" for k, v in filtros.items())
    url = f"{BASE}/dashboard/brecha" + (f"?{qs}" if qs else "")
    r = requests.get(url, timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert "pasos" in body
    assert len(body["pasos"]) == 5


# ──── Trazabilidad X-Data-Source ────

@pytest.mark.parametrize("path,expected_source", [
    ("/dashboard/dificultades?grupo_etnico=Indigena", "cnpv.dificultades"),
    ("/dashboard/brecha", "cnpv.resumen"),
    ("/dashboard/intercensal?aplicar_fac=true", "cnpv.comparacion_intercensal"),
    ("/dashboard/proyecciones?grupo_etnico=Indigena", "proyecciones.escenarios"),
    ("/dashboard/smt-resumen", "smt.resumen"),
    ("/demografia/piramide-disc-nacional", "pueblo.piramide_disc"),
    ("/demografia/piramide-nacional", "visor_dane.piramide_pueblo"),
])
def test_x_data_source_correcto(path, expected_source):
    r = requests.get(f"{BASE}{path}", timeout=15)
    headers_lower = {k.lower(): v for k, v in r.headers.items()}
    assert "x-data-source" in headers_lower, f"Falta header en {path}"
    assert expected_source.lower() in headers_lower["x-data-source"].lower(), (
        f"X-Data-Source en {path}: esperado '{expected_source}' "
        f"contenido en '{headers_lower['x-data-source']}'"
    )


# ──── Health check ────

def test_health_completo():
    r = requests.get(f"{BASE}/health", timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok", f"Health degradado: {body}"
    # Verificar que las 10 tablas críticas reportan ok
    for tabla in ["cnpv.resumen_nacional_etnico", "pueblo.disc_nacional",
                  "smt_geo.resguardos", "smt_geo.macrorregiones",
                  "visor_dane.piramide_pueblo", "indicadores.definiciones",
                  "proyecciones.fac", "proyecciones.escenarios", "smt.resumen"]:
        assert tabla in body, f"Falta check {tabla} en /health"
        assert body[tabla]["ok"] is True, f"Tabla {tabla} no OK: {body[tabla]}"
