"""
K04 · Tests de filtro discapacidad = '1' en endpoints /conflicto
Valida que los 3 endpoints afectados por el bug semántico solo retornan
víctimas indígenas CON capacidades diversas (discapacidad='1').

Cifras canónicas de validación Playwright real 2026-05-06:
  - Total víctimas nacionales con disc: 37.562
  - Macrorregión NORTE: ≤ 6.907
  - Departamento La Guajira (cod=44): ≤ 1.007
"""

import pytest
import requests

BASE_URL = "http://localhost:8095/api/v1/conflicto"
CANON_TOTAL = 37_562


# ---------------------------------------------------------------------------
# 1. /victimas/por-pueblo · sin filtros geográficos
# ---------------------------------------------------------------------------

def test_por_pueblo_solo_disc():
    """total_victimas (suma de filas) debe ser ≤ 37.562."""
    r = requests.get(f"{BASE_URL}/victimas/por-pueblo", timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:200]}"
    body = r.json()
    total = body.get("total_victimas", None)
    assert total is not None, "Clave 'total_victimas' ausente en respuesta"
    assert total <= CANON_TOTAL, (
        f"total_victimas={total} supera el máximo esperado {CANON_TOTAL}. "
        "Probablemente el filtro discapacidad='1' no se aplicó."
    )


# ---------------------------------------------------------------------------
# 2. /victimas/por-hecho · sin filtros geográficos
# ---------------------------------------------------------------------------

def test_por_hecho_solo_disc():
    """Sumatoria de total_victimas en todas las filas debe ser ≤ 37.562."""
    r = requests.get(f"{BASE_URL}/victimas/por-hecho", timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:200]}"
    body = r.json()
    total = body.get("total_victimas", None)
    assert total is not None, "Clave 'total_victimas' ausente en respuesta"
    assert total <= CANON_TOTAL, (
        f"total_victimas={total} supera el máximo esperado {CANON_TOTAL}. "
        "Probablemente el filtro discapacidad='1' no se aplicó."
    )


# ---------------------------------------------------------------------------
# 3. /victimas/por-tipo · cifra exacta 37.562
# ---------------------------------------------------------------------------

def test_por_tipo_solo_disc():
    """Sumatoria de total_victimas debe ser EXACTAMENTE 37.562 (matching canónico)."""
    r = requests.get(f"{BASE_URL}/victimas/por-tipo", timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:200]}"
    body = r.json()
    total = body.get("total_victimas", None)
    assert total is not None, "Clave 'total_victimas' ausente en respuesta"
    assert total == CANON_TOTAL, (
        f"total_victimas={total} debe ser exactamente {CANON_TOTAL}. "
        "Bug si es mayor (sin filtro disc) o menor (filtro incorrecto)."
    )


# ---------------------------------------------------------------------------
# 4. /victimas/por-pueblo · filtro macrorregión NORTE
# ---------------------------------------------------------------------------

def test_por_pueblo_con_filtro_norte():
    """Con cod_macro=NORTE, total_victimas debe ser ≤ 6.907."""
    r = requests.get(
        f"{BASE_URL}/victimas/por-pueblo",
        params={"cod_macro": "NORTE"},
        timeout=15,
    )
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:200]}"
    body = r.json()
    total = body.get("total_victimas", None)
    assert total is not None, "Clave 'total_victimas' ausente en respuesta"
    assert total <= 6_907, (
        f"total_victimas NORTE={total} supera 6.907 (cifra canónica Playwright). "
        "Filtro geográfico o de discapacidad no aplicado."
    )


# ---------------------------------------------------------------------------
# 5. /victimas/por-pueblo · filtro departamento La Guajira (cod=44)
# ---------------------------------------------------------------------------

def test_por_pueblo_con_filtro_la_guajira():
    """Con cod_dpto=44, total_victimas debe ser ≤ 1.007."""
    r = requests.get(
        f"{BASE_URL}/victimas/por-pueblo",
        params={"cod_dpto": "44"},
        timeout=15,
    )
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:200]}"
    body = r.json()
    total = body.get("total_victimas", None)
    assert total is not None, "Clave 'total_victimas' ausente en respuesta"
    assert total <= 1_007, (
        f"total_victimas La Guajira={total} supera 1.007 (cifra canónica Playwright). "
        "Filtro geográfico o de discapacidad no aplicado."
    )
