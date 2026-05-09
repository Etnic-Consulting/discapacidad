"""
test_dashboard.py · Cobertura >= 55% de app/routers/dashboard.py

Estrategia: AsyncClient + dependency_overrides para get_db (sin BD real).
El router dashboard NO requiere auth (router = APIRouter() sin global dep).

Endpoints cubiertos:
  GET /api/v1/dashboard/                          resumen_nacional (200 + 404 + 500)
  GET /api/v1/dashboard/prevalencia/departamento  prevalencia_por_departamento
  GET /api/v1/dashboard/prevalencia/municipio     prevalencia_indigena_municipio
  GET /api/v1/dashboard/dificultades              dificultades_radar
  GET /api/v1/dashboard/filtros                   filtros_cascada
  GET /api/v1/dashboard/brecha                    brecha_certificacion
  GET /api/v1/dashboard/salud                     salud_embudo
  GET /api/v1/dashboard/intercensal               comparacion_intercensal
  GET /api/v1/dashboard/smt-resumen               smt_resumen
  GET /api/v1/dashboard/proyecciones              proyecciones_prevalencia
  GET /api/v1/dashboard/panorama-kpis             panorama_kpis
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import get_db
from app.filters import FiltroGeografico


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row(mapping: dict):
    row = MagicMock()
    row._mapping = mapping
    return row


def _result(rows: list[dict] | None = None, scalar=None, first_row: dict | None = None):
    result = MagicMock()
    _rows = [_row(r) for r in (rows or [])]
    # Use side_effect so each __iter__ call returns a fresh iterator
    result.__iter__ = MagicMock(side_effect=lambda: iter(list(_rows)))
    result.first.return_value = _row(first_row) if first_row is not None else None
    result.scalar.return_value = scalar
    result.fetchall.return_value = list(_rows)
    return result


def _make_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client():
    db = _make_db()
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        c._mock_db = db
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /api/v1/dashboard/   · resumen_nacional
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_resumen_nacional_200(client):
    """Con datos → 200."""
    rows = [
        {"grupo_etnico": "Indigena", "pob_total": 1173000, "pob_disc": 100000,
         "prevalencia_pct": 8.53, "tasa_x_1000": 85.3},
        {"grupo_etnico": "Afrodescendiente", "pob_total": 4671000, "pob_disc": 300000,
         "prevalencia_pct": 6.42, "tasa_x_1000": 64.2},
    ]
    client._mock_db.execute.return_value = _result(rows=rows)
    r = await client.get("/api/v1/dashboard/")
    assert r.status_code == 200
    body = r.json()
    assert body["periodo"] == "2018"
    assert len(body["data"]) == 2


@pytest.mark.asyncio
async def test_resumen_nacional_404(client):
    """Sin datos para el periodo → 404."""
    client._mock_db.execute.return_value = _result(rows=[])
    r = await client.get("/api/v1/dashboard/?periodo=1900")
    assert r.status_code == 404
    assert "1900" in r.json()["detail"]


@pytest.mark.asyncio
async def test_resumen_nacional_periodo_custom(client):
    """Periodo personalizado en query param."""
    rows = [{"grupo_etnico": "Indigena", "pob_total": 100, "pob_disc": 10,
              "prevalencia_pct": 10.0, "tasa_x_1000": 100.0}]
    client._mock_db.execute.return_value = _result(rows=rows)
    r = await client.get("/api/v1/dashboard/?periodo=2005")
    assert r.status_code == 200
    assert r.json()["periodo"] == "2005"


@pytest.mark.asyncio
async def test_resumen_nacional_500(client):
    """DB error → 500."""
    client._mock_db.execute.side_effect = Exception("DB down")
    r = await client.get("/api/v1/dashboard/")
    assert r.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/v1/dashboard/prevalencia/departamento
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_prevalencia_dpto_sin_filtros(client):
    """Sin filtros → 200 con data."""
    # resolver_filtros hace db.execute internamente; mock retorna vacío (sin restricciones)
    rows_prev = [
        {"cod_dpto": "05", "nom_dpto": "Antioquia", "grupo_etnico": "Indigena",
         "pob_total": 500, "pob_disc": 40, "pob_no_disc": 460,
         "tasa_x_1000": 80.0, "prevalencia_pct": 8.0},
    ]

    call_count = 0

    async def side_effect(query, params=None):
        nonlocal call_count
        call_count += 1
        # resolver_filtros no hace query si no hay filtros geo
        # la query principal es la primera
        return _result(rows=rows_prev)

    client._mock_db.execute.side_effect = side_effect
    r = await client.get("/api/v1/dashboard/prevalencia/departamento")
    assert r.status_code == 200
    body = r.json()
    assert "data" in body
    assert body["total"] == 1


@pytest.mark.asyncio
async def test_prevalencia_dpto_con_grupo_etnico(client):
    """Con grupo_etnico=Indigena."""
    client._mock_db.execute.return_value = _result(rows=[])
    r = await client.get("/api/v1/dashboard/prevalencia/departamento?grupo_etnico=Indigena")
    assert r.status_code == 200
    assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_prevalencia_dpto_500(client):
    client._mock_db.execute.side_effect = Exception("err")
    r = await client.get("/api/v1/dashboard/prevalencia/departamento")
    assert r.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/v1/dashboard/prevalencia/municipio
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_prevalencia_mpio_200(client):
    rows = [
        {"cod_dpto": "05", "cod_mpio": "05001", "nom_mpio": "Medellin",
         "pob_indigena": 1500, "con_disc": 120, "tasa_x_1000": 80.0},
    ]
    client._mock_db.execute.return_value = _result(rows=rows)
    r = await client.get("/api/v1/dashboard/prevalencia/municipio")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["data"][0]["cod_mpio"] == "05001"


@pytest.mark.asyncio
async def test_prevalencia_mpio_con_cod_dpto(client):
    """Filtro cod_dpto."""
    client._mock_db.execute.return_value = _result(rows=[])
    r = await client.get("/api/v1/dashboard/prevalencia/municipio?cod_dpto=05")
    assert r.status_code == 200
    assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_prevalencia_mpio_n_min_borde(client):
    """n_min=0 incluye todos."""
    client._mock_db.execute.return_value = _result(rows=[])
    r = await client.get("/api/v1/dashboard/prevalencia/municipio?n_min=0")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_prevalencia_mpio_500(client):
    client._mock_db.execute.side_effect = Exception("err")
    r = await client.get("/api/v1/dashboard/prevalencia/municipio")
    assert r.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/v1/dashboard/dificultades
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dificultades_200(client):
    rows = [
        {"grupo_etnico": "Indigena", "dificultad": "vision",
         "pob_total": 1000, "con_dificultad": 50, "tasa_x_1000": 50.0},
        {"grupo_etnico": "Indigena", "dificultad": "movilidad",
         "pob_total": 1000, "con_dificultad": 30, "tasa_x_1000": 30.0},
    ]
    client._mock_db.execute.return_value = _result(rows=rows)
    r = await client.get("/api/v1/dashboard/dificultades")
    assert r.status_code == 200
    body = r.json()
    assert len(body["data"]) == 2


@pytest.mark.asyncio
async def test_dificultades_con_grupo_etnico(client):
    client._mock_db.execute.return_value = _result(rows=[])
    r = await client.get("/api/v1/dashboard/dificultades?grupo_etnico=Indigena")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_dificultades_500(client):
    client._mock_db.execute.side_effect = Exception("err")
    r = await client.get("/api/v1/dashboard/dificultades")
    assert r.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/v1/dashboard/filtros
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_filtros_sin_params(client):
    """Sin params → devuelve departamentos."""
    rows_dptos = [
        {"cod_dpto": "05", "nom_dpto": "Antioquia"},
        {"cod_dpto": "11", "nom_dpto": "Bogota"},
    ]
    client._mock_db.execute.return_value = _result(rows=rows_dptos)
    r = await client.get("/api/v1/dashboard/filtros")
    assert r.status_code == 200
    body = r.json()
    assert "departamentos" in body
    assert len(body["departamentos"]) == 2


@pytest.mark.asyncio
async def test_filtros_con_cod_dpto(client):
    """Con cod_dpto → agrega municipios, pueblos y resguardos."""
    dptos = [{"cod_dpto": "05", "nom_dpto": "Antioquia"}]
    mpios = [{"cod_mpio": "05001", "nom_mpio": "Medellin", "cod_dpto": "05"}]
    pueblos = [{"cod_pueblo": "720", "pueblo": "Embera"}]
    resguardos = [{"cod_resguardo": "RG-001", "nombre": "Resguardo1",
                   "pueblo_onic": "Embera", "nom_departamento": "Antioquia",
                   "nom_municipio": "Medellin", "cod_mpio": "05001",
                   "poblacion_total": 500}]

    call_count = 0

    async def side_effect(query, params=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _result(rows=dptos)       # departamentos always
        elif call_count == 2:
            return _result(rows=mpios)       # mpios del dpto
        elif call_count == 3:
            return _result(rows=pueblos)     # pueblos del dpto
        else:
            return _result(rows=resguardos)  # resguardos del dpto

    client._mock_db.execute.side_effect = side_effect
    r = await client.get("/api/v1/dashboard/filtros?cod_dpto=05")
    assert r.status_code == 200
    body = r.json()
    assert "municipios" in body
    assert "pueblos" in body
    assert "resguardos" in body


@pytest.mark.asyncio
async def test_filtros_con_cod_mpio(client):
    """Con cod_mpio → agrega pueblos y resguardos del municipio."""
    dptos = [{"cod_dpto": "05", "nom_dpto": "Antioquia"}]
    pueblos_mpio = [{"cod_pueblo": "720", "pueblo": "Embera",
                     "poblacion": 1200, "pct_en_mpio": 45.0, "es_dominante": True}]
    resguardos_mpio = [{"cod_resguardo": "RG-001", "nombre": "Resguardo1",
                        "pueblo_onic": "Embera", "nom_departamento": "Antioquia",
                        "nom_municipio": "Medellin", "cod_mpio": "05001",
                        "poblacion_total": 500}]

    call_count = 0

    async def side_effect(query, params=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _result(rows=dptos)
        elif call_count == 2:
            return _result(rows=pueblos_mpio)
        else:
            return _result(rows=resguardos_mpio)

    client._mock_db.execute.side_effect = side_effect
    r = await client.get("/api/v1/dashboard/filtros?cod_mpio=05001")
    assert r.status_code == 200
    body = r.json()
    assert "pueblos" in body
    assert "resguardos" in body


@pytest.mark.asyncio
async def test_filtros_con_cod_macro(client):
    """Con cod_macro → devuelve dptos/mpios/pueblos/resguardos de la macro."""
    dptos = [{"cod_dpto": "05", "nom_dpto": "Antioquia"}]
    mpios = [{"cod_mpio": "05001", "nom_mpio": "Medellin", "cod_dpto": "05"}]
    pueblos = [{"cod_pueblo": "720", "pueblo": "Embera"}]
    resguardos = [{"cod_resguardo": "RG-001", "nombre": "Resguardo1",
                   "pueblo_onic": "Embera", "nom_departamento": "Antioquia",
                   "nom_municipio": "Medellin", "cod_mpio": "05001"}]

    calls = [dptos, dptos, mpios, pueblos, resguardos]
    call_count = 0

    async def side_effect(query, params=None):
        nonlocal call_count
        idx = min(call_count, len(calls) - 1)
        call_count += 1
        return _result(rows=calls[idx])

    client._mock_db.execute.side_effect = side_effect
    r = await client.get("/api/v1/dashboard/filtros?cod_macro=NORTE")
    assert r.status_code == 200
    body = r.json()
    assert "departamentos" in body


@pytest.mark.asyncio
async def test_filtros_500(client):
    client._mock_db.execute.side_effect = Exception("err")
    r = await client.get("/api/v1/dashboard/filtros")
    assert r.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/v1/dashboard/brecha
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_brecha_nacional(client):
    """Brecha sin filtros · 3 queries (cnpv + rlcpd + smt)."""
    row_cnpv = {"pob_total": 1173000, "pob_disc": 100000}
    rlcpd_scalar = 500000
    smt_scalar = 1200

    call_count = 0

    async def side_effect(query, params=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # cnpv.prevalencia_etnia_dpto
            r = MagicMock()
            m = MagicMock()
            m._mapping = row_cnpv
            r.first.return_value = m
            return r
        elif call_count == 2:
            # rlcpd scalar
            r = MagicMock()
            r.scalar.return_value = rlcpd_scalar
            return r
        else:
            # smt scalar
            r = MagicMock()
            r.scalar.return_value = smt_scalar
            return r

    client._mock_db.execute.side_effect = side_effect
    r = await client.get("/api/v1/dashboard/brecha")
    assert r.status_code == 200
    body = r.json()
    assert "pasos" in body
    assert len(body["pasos"]) == 5


@pytest.mark.asyncio
async def test_brecha_con_cod_dpto(client):
    """Brecha filtrada por dpto.

    Con cod_dpto, resolver_filtros hace 1 query (municipios del dpto).
    Luego brecha hace: cnpv (first), rlcpd (scalar), smt (scalar).
    """
    row_cnpv = {"pob_total": 50000, "pob_disc": 4000}

    def _scalar_r(v):
        r = MagicMock()
        r.scalar.return_value = v
        r.fetchall.return_value = []
        return r

    def _first_r(mapping):
        r = MagicMock()
        m = MagicMock()
        m._mapping = mapping
        r.first.return_value = m
        r.fetchall.return_value = []
        return r

    call_count = 0

    async def side_effect(query, params=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # resolver_filtros: geo.municipios fetchall
            return _scalar_r(None)
        elif call_count == 2:
            # cnpv.prevalencia_etnia_dpto → first()
            return _first_r(row_cnpv)
        elif call_count == 3:
            # rlcpd scalar
            return _scalar_r(100000)
        else:
            # smt scalar
            return _scalar_r(50)

    client._mock_db.execute.side_effect = side_effect
    r = await client.get("/api/v1/dashboard/brecha?cod_dpto=05")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_brecha_500(client):
    client._mock_db.execute.side_effect = Exception("err")
    r = await client.get("/api/v1/dashboard/brecha")
    assert r.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/v1/dashboard/salud
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_salud_200(client):
    rows = [
        {"grupo_etnico": "Indigena", "variable": "afiliacion",
         "categoria": "ninguna", "valor": 5000, "total_grupo": 100000},
    ]
    client._mock_db.execute.return_value = _result(rows=rows)
    r = await client.get("/api/v1/dashboard/salud")
    assert r.status_code == 200
    body = r.json()
    assert body["periodo"] == "2018"
    assert len(body["data"]) == 1


@pytest.mark.asyncio
async def test_salud_con_cod_dpto(client):
    client._mock_db.execute.return_value = _result(rows=[])
    r = await client.get("/api/v1/dashboard/salud?cod_dpto=05")
    assert r.status_code == 200
    assert r.json()["data"] == []


@pytest.mark.asyncio
async def test_salud_500(client):
    client._mock_db.execute.side_effect = Exception("err")
    r = await client.get("/api/v1/dashboard/salud")
    assert r.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/v1/dashboard/intercensal
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_intercensal_sin_filtro(client):
    rows = [
        {"grupo_etnico": "Indigena", "periodo": "2005", "pob_total": 900000,
         "pob_disc": 72000, "prevalencia_pct": 8.0, "tasa_x_1000": 80.0},
        {"grupo_etnico": "Indigena", "periodo": "2018", "pob_total": 1173000,
         "pob_disc": 100000, "prevalencia_pct": 8.53, "tasa_x_1000": 85.3},
    ]
    client._mock_db.execute.return_value = _result(rows=rows)
    r = await client.get("/api/v1/dashboard/intercensal")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert body["fac_aplicado"] is False


@pytest.mark.asyncio
async def test_intercensal_con_grupo_etnico(client):
    client._mock_db.execute.return_value = _result(rows=[])
    r = await client.get("/api/v1/dashboard/intercensal?grupo_etnico=Indigena")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_intercensal_aplicar_fac(client):
    """Con aplicar_fac=true · intenta leer tabla proyecciones.fac."""
    rows_inter = [
        {"grupo_etnico": "Indigena", "periodo": "2005", "pob_total": 900000,
         "pob_disc": 72000, "prevalencia_pct": 8.0, "tasa_x_1000": 80.0},
    ]
    fac_rows = [
        MagicMock(__getitem__=lambda self, k: {"Indigena": "Indigena", 0: "Indigena",
                   1: 1.3, 2: 1.1, 3: 1.5}[k]),
    ]
    # fac_result debe ser iterable con rows tipo (grupo_etnico, fac, ic_inf, ic_sup)
    fac_row_tuple = ("Indigena", 1.3, 1.1, 1.5)

    call_count = 0

    async def side_effect(query, params=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _result(rows=rows_inter)
        # segunda llamada: tabla fac
        r = MagicMock()
        r.fetchall.return_value = [fac_row_tuple]
        return r

    client._mock_db.execute.side_effect = side_effect
    r = await client.get("/api/v1/dashboard/intercensal?aplicar_fac=true")
    assert r.status_code == 200
    body = r.json()
    assert body["fac_aplicado"] is True


@pytest.mark.asyncio
async def test_intercensal_fac_tabla_ausente(client):
    """Si tabla fac da error → devuelve advertencia pero 200."""
    rows_inter = [
        {"grupo_etnico": "Indigena", "periodo": "2005", "pob_total": 900000,
         "pob_disc": 72000, "prevalencia_pct": 8.0, "tasa_x_1000": 80.0},
    ]

    call_count = 0

    async def side_effect(query, params=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _result(rows=rows_inter)
        raise Exception("tabla proyecciones.fac no existe")

    client._mock_db.execute.side_effect = side_effect
    r = await client.get("/api/v1/dashboard/intercensal?aplicar_fac=true")
    assert r.status_code == 200
    body = r.json()
    assert body["fac_aplicado"] is False
    assert body["advertencia"] is not None


@pytest.mark.asyncio
async def test_intercensal_500(client):
    client._mock_db.execute.side_effect = Exception("err")
    r = await client.get("/api/v1/dashboard/intercensal")
    assert r.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/v1/dashboard/smt-resumen
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_smt_resumen_200(client):
    """Endpoint hace 2 queries: (1) auto-selecciona periodo, (2) lee datos.

    Responde: {periodo, total_dimensiones, total_categorias, dimensiones, data, agrupado}
    """
    periodo_row = {"periodo": "2026-F1"}
    data_rows = [
        {"dimension": "edad", "categoria": "15-29", "valor": 400, "pct": 33.3},
        {"dimension": "edad", "categoria": "30-44", "valor": 350, "pct": 29.2},
    ]
    call_count = 0

    async def side_effect(query, params=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # query periodo más reciente → first()
            return _result(first_row=periodo_row)
        return _result(rows=data_rows)

    client._mock_db.execute.side_effect = side_effect
    r = await client.get("/api/v1/dashboard/smt-resumen")
    assert r.status_code == 200
    body = r.json()
    assert body["periodo"] == "2026-F1"
    assert body["total_categorias"] == 2
    assert body["total_dimensiones"] == 1
    assert "agrupado" in body


@pytest.mark.asyncio
async def test_smt_resumen_con_dimension(client):
    """Con dimension filtro · también hace 2 queries."""
    call_count = 0

    async def side_effect(query, params=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _result(first_row={"periodo": "2026-F1"})
        return _result(rows=[])

    client._mock_db.execute.side_effect = side_effect
    r = await client.get("/api/v1/dashboard/smt-resumen?dimension=edad")
    assert r.status_code == 200
    assert r.json()["total_categorias"] == 0


@pytest.mark.asyncio
async def test_smt_resumen_con_periodo_explicito(client):
    """Con periodo explícito · omite la query de auto-selección."""
    data_rows = [
        {"dimension": "tipo", "categoria": "visual", "valor": 200, "pct": 25.0},
    ]
    client._mock_db.execute.return_value = _result(rows=data_rows)
    r = await client.get("/api/v1/dashboard/smt-resumen?periodo=2026-01")
    assert r.status_code == 200
    body = r.json()
    assert body["periodo"] == "2026-01"
    assert body["total_categorias"] == 1


@pytest.mark.asyncio
async def test_smt_resumen_500(client):
    client._mock_db.execute.side_effect = Exception("err")
    r = await client.get("/api/v1/dashboard/smt-resumen")
    assert r.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/v1/dashboard/proyecciones
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_proyecciones_200(client):
    rows = [
        {"año": 2005, "escenario": "Base", "prevalencia_pct": 8.0,
         "ic_inferior_pct": 6.8, "ic_superior_pct": 9.2,
         "es_observado": True, "es_ajustado_fac": True, "fac_aplicado": 1.3},
        {"año": 2018, "escenario": "Base", "prevalencia_pct": 8.53,
         "ic_inferior_pct": 7.25, "ic_superior_pct": 9.81,
         "es_observado": True, "es_ajustado_fac": False, "fac_aplicado": None},
        {"año": 2025, "escenario": "Base", "prevalencia_pct": 9.0,
         "ic_inferior_pct": 7.65, "ic_superior_pct": 10.35,
         "es_observado": False, "es_ajustado_fac": False, "fac_aplicado": None},
    ]
    client._mock_db.execute.return_value = _result(rows=rows)
    r = await client.get("/api/v1/dashboard/proyecciones")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3
    assert "metadata" in body
    assert body["grupo_etnico"] == "Indigena"


@pytest.mark.asyncio
async def test_proyecciones_con_grupo_etnico(client):
    client._mock_db.execute.return_value = _result(rows=[])
    r = await client.get("/api/v1/dashboard/proyecciones?grupo_etnico=Afrodescendiente")
    assert r.status_code == 200
    assert r.json()["grupo_etnico"] == "Afrodescendiente"


@pytest.mark.asyncio
async def test_proyecciones_con_escenario(client):
    client._mock_db.execute.return_value = _result(rows=[])
    r = await client.get("/api/v1/dashboard/proyecciones?escenario=Optimista")
    assert r.status_code == 200
    assert r.json()["escenario_filtro"] == "Optimista"


@pytest.mark.asyncio
async def test_proyecciones_periodo_rango(client):
    client._mock_db.execute.return_value = _result(rows=[])
    r = await client.get("/api/v1/dashboard/proyecciones?periodo_inicio=2018&periodo_fin=2025")
    assert r.status_code == 200
    assert r.json()["periodo_inicio"] == 2018
    assert r.json()["periodo_fin"] == 2025


@pytest.mark.asyncio
async def test_proyecciones_500(client):
    client._mock_db.execute.side_effect = Exception("err")
    r = await client.get("/api/v1/dashboard/proyecciones")
    assert r.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/v1/dashboard/panorama-kpis
# ---------------------------------------------------------------------------

def _scalar_result(value):
    r = MagicMock()
    r.scalar.return_value = value
    r.first.return_value = None
    r.fetchall.return_value = []
    return r


def _first_result_positional(values: list):
    """Row accedido por índice entero (row[0], row[1]...)."""
    r = MagicMock()
    row = MagicMock()
    row.__getitem__ = MagicMock(side_effect=lambda i: values[i])
    r.first.return_value = row
    r.scalar.return_value = None
    r.fetchall.return_value = []
    return r


def _first_result(mapping):
    """Row accedido por _mapping (dict)."""
    r = MagicMock()
    m = MagicMock()
    m._mapping = mapping
    r.first.return_value = m
    r.scalar.return_value = None
    r.fetchall.return_value = []
    return r


@pytest.mark.asyncio
async def test_panorama_kpis_nacional(client):
    """Nacional (sin filtros).

    Secuencia queries:
      1. pueblo.disc_nacional (first, índice positional: pob_total, pob_disc, tasa)
      2. COUNT(DISTINCT cod_pueblo) pueblos (scalar)
      3. COUNT(*) smt.respuestas_formulario caracterizados (scalar)
      4. COUNT FILTER sin cert brecha (scalar)
      5. COUNT(*) victimas.universo (scalar)
      6. COUNT(DISTINCT pueblo_imputado) (scalar)
    """
    responses = [
        _first_result_positional([1173000, 100000, 85.3]),  # disc_nacional
        _scalar_result(115),    # pueblos
        _scalar_result(1200),   # caracterizados
        _scalar_result(900),    # sin cert
        _scalar_result(5000),   # victimas
        _scalar_result(80),     # pueblos_con_victimas
    ]
    idx = 0

    async def side_effect(query, params=None):
        nonlocal idx
        r = responses[idx] if idx < len(responses) else _scalar_result(0)
        idx += 1
        return r

    client._mock_db.execute.side_effect = side_effect
    r = await client.get("/api/v1/dashboard/panorama-kpis")
    assert r.status_code == 200
    body = r.json()
    assert body["scope"] == "nacional"
    assert "total_personas" in body
    assert "pueblos" in body
    assert "caracterizados_smt" in body


@pytest.mark.asyncio
async def test_panorama_kpis_scope_dpto(client):
    """Scope=dpto · cod_dpto=05 (row acceso positional)."""
    responses = [
        _first_result_positional([50000, 4000, 80.0]),  # prevalencia_etnia_dpto
        _scalar_result(12),   # pueblos
        _scalar_result(100),  # caracterizados
        _scalar_result(80),   # sin cert
        _scalar_result(300),  # victimas
        _scalar_result(8),    # pueblos_con_victimas
    ]
    idx = 0

    async def side_effect(query, params=None):
        nonlocal idx
        r = responses[idx] if idx < len(responses) else _scalar_result(0)
        idx += 1
        return r

    client._mock_db.execute.side_effect = side_effect
    r = await client.get("/api/v1/dashboard/panorama-kpis?cod_dpto=05")
    assert r.status_code == 200
    body = r.json()
    assert body["scope"] == "dpto"


@pytest.mark.asyncio
async def test_panorama_kpis_scope_pueblo(client):
    """Scope=pueblo · cod_pueblo=720.

    Secuencia:
      1. pueblo.pueblo_municipio SUM(poblacion) → first()[0]
      2. pueblo.disc_nacional → first()[0], [1], [2]
      3. pueblos_count = 1 (ya se conoce, no hay query)
      4. caracterizados scalar
      5. sin cert scalar
      6. victimas scalar
      7. pueblos_con_victimas scalar
    """
    responses = [
        _first_result_positional([12000]),              # pueblo_municipio SUM
        _first_result_positional([1000, 12000, 83.3]),  # disc_nacional
        # pueblos_count=1 (no query)
        _scalar_result(50),    # caracterizados
        _scalar_result(40),    # sin cert
        _scalar_result(200),   # victimas
        _scalar_result(1),     # pueblos_con_victimas
    ]
    idx = 0

    async def side_effect(query, params=None):
        nonlocal idx
        r = responses[idx] if idx < len(responses) else _scalar_result(0)
        idx += 1
        return r

    client._mock_db.execute.side_effect = side_effect
    r = await client.get("/api/v1/dashboard/panorama-kpis?cod_pueblo=720")
    assert r.status_code == 200
    body = r.json()
    assert body["scope"] == "pueblo"


@pytest.mark.asyncio
async def test_panorama_kpis_scope_mpio(client):
    """Scope=mpio · cod_mpio=05001 (row acceso positional)."""
    responses = [
        _first_result_positional([1500, 120, 80.0]),  # prevalencia_etnia_mpio
        _scalar_result(3),   # pueblos
        _scalar_result(20),  # caracterizados
        _scalar_result(15),  # sin cert
        _scalar_result(50),  # victimas
        _scalar_result(2),   # pueblos_con_victimas
    ]
    idx = 0

    async def side_effect(query, params=None):
        nonlocal idx
        r = responses[idx] if idx < len(responses) else _scalar_result(0)
        idx += 1
        return r

    client._mock_db.execute.side_effect = side_effect
    r = await client.get("/api/v1/dashboard/panorama-kpis?cod_mpio=05001")
    assert r.status_code == 200
    assert r.json()["scope"] == "mpio"


@pytest.mark.asyncio
async def test_panorama_kpis_sin_caracterizados_brecha_none(client):
    """caracterizados_smt=0 → brecha_certificacion=None · cobertura_smt=None."""
    responses = [
        _first_result_positional([1173000, 100000, 85.3]),  # disc_nacional
        _scalar_result(115),  # pueblos
        _scalar_result(0),    # caracterizados = 0  → brecha se omite
        _scalar_result(5000), # victimas.universo
        _scalar_result(80),   # pueblos_con_victimas
    ]
    idx = 0

    async def side_effect(query, params=None):
        nonlocal idx
        r = responses[idx] if idx < len(responses) else _scalar_result(0)
        idx += 1
        return r

    client._mock_db.execute.side_effect = side_effect
    r = await client.get("/api/v1/dashboard/panorama-kpis")
    assert r.status_code == 200
    body = r.json()
    # brecha_certificacion is None when caracterizados_smt==0 (no query for cert)
    assert body["brecha_certificacion"] is None
    # cobertura_smt = 0/total*100 = 0.0 when caracterizados=0 but total_personas>0
    assert body["cobertura_smt"] == 0.0


@pytest.mark.asyncio
async def test_panorama_kpis_500(client):
    client._mock_db.execute.side_effect = Exception("err")
    r = await client.get("/api/v1/dashboard/panorama-kpis")
    assert r.status_code == 500
