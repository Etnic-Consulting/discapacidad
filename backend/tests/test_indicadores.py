"""
test_indicadores.py · Cobertura >= 55% de app/routers/indicadores.py

Estrategia: AsyncClient + dependency_overrides para get_db y get_current_user.
No se conecta a Postgres real. Todos los returns de db.execute son mocks.

Endpoints cubiertos:
  GET  /api/v1/indicadores/               listar_definiciones
  GET  /api/v1/indicadores/valores        valores_indicadores
  GET  /api/v1/indicadores/serie-tiempo/{cod}  serie_tiempo (200 + 404)
  POST /api/v1/indicadores/recalcular     recalcular_indicadores
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import get_db
from app.routers.auth import get_current_user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row(mapping: dict):
    """Crea un row SQLAlchemy-like con _mapping."""
    row = MagicMock()
    row._mapping = mapping
    return row


def _result(rows: list[dict] | None = None, scalar=None, first_row: dict | None = None):
    """Construye un result mock que imita AsyncSession.execute()."""
    result = MagicMock()
    _rows = [_row(r) for r in (rows or [])]
    # side_effect so each __iter__ call returns a fresh iterator (not a shared exhausted one)
    result.__iter__ = MagicMock(side_effect=lambda: iter(list(_rows)))

    if first_row is not None:
        result.first.return_value = _row(first_row)
    else:
        result.first.return_value = None

    result.scalar.return_value = scalar
    result.fetchall.return_value = list(_rows)
    return result


def _make_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


def _fake_user():
    user = MagicMock()
    user.id = 1
    user.username = "testuser"
    user.rol = "admin"
    user.activo = True
    return user


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client():
    db = _make_db()
    user = _fake_user()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        c._mock_db = db   # exponer para configurar en cada test
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /api/v1/indicadores/   · listar_definiciones
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_listar_definiciones_vacio(client):
    """Sin filas en BD devuelve 200 con data=[]."""
    client._mock_db.execute.return_value = _result(rows=[])
    r = await client.get("/api/v1/indicadores/")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert body["data"] == []


@pytest.mark.asyncio
async def test_listar_definiciones_con_datos(client):
    """Con filas devuelve total correcto."""
    rows = [
        {"id": 1, "codigo": "IND-01", "nombre": "Tasa prevalencia",
         "grupo": "salud", "formula": "...", "meta": None,
         "fuente_primaria": "CNPV", "fuente_cruce": None,
         "unidad": "x1000", "descripcion": "Desc"},
        {"id": 2, "codigo": "IND-02", "nombre": "Brecha",
         "grupo": "social", "formula": "...", "meta": 0.5,
         "fuente_primaria": "SMT", "fuente_cruce": "RLCPD",
         "unidad": "pct", "descripcion": "Desc2"},
    ]
    client._mock_db.execute.return_value = _result(rows=rows)
    r = await client.get("/api/v1/indicadores/")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert len(body["data"]) == 2
    assert body["data"][0]["codigo"] == "IND-01"


@pytest.mark.asyncio
async def test_listar_definiciones_500(client):
    """Si db.execute lanza excepción → 500."""
    client._mock_db.execute.side_effect = Exception("DB error")
    r = await client.get("/api/v1/indicadores/")
    assert r.status_code == 500
    assert "Error consultando definiciones" in r.json()["detail"]


# ---------------------------------------------------------------------------
# GET /api/v1/indicadores/valores   · valores_indicadores
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_valores_sin_filtros(client):
    """Sin filtros · devuelve 200 con datos."""
    rows = [
        {"cod_indicador": "IND-01", "indicador_nombre": "Tasa",
         "grupo": "salud", "unidad": "x1000",
         "periodo": "2018", "nivel_geo": "nacional", "cod_geo": None,
         "nombre_geo": None, "grupo_etnico": "Indigena", "pueblo": None,
         "valor": 85.3, "numerador": 100, "denominador": 1173,
         "confianza": 0.95},
    ]
    client._mock_db.execute.return_value = _result(rows=rows)
    r = await client.get("/api/v1/indicadores/valores")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1


@pytest.mark.asyncio
async def test_valores_con_filtro_periodo(client):
    """Filtro periodo=2018 · query se ejecuta y devuelve datos."""
    client._mock_db.execute.return_value = _result(rows=[
        {"cod_indicador": "IND-01", "indicador_nombre": "Tasa",
         "grupo": "salud", "unidad": "x1000",
         "periodo": "2018", "nivel_geo": "nacional", "cod_geo": None,
         "nombre_geo": None, "grupo_etnico": "Indigena", "pueblo": None,
         "valor": 85.3, "numerador": 100, "denominador": 1173,
         "confianza": 0.95},
    ])
    r = await client.get("/api/v1/indicadores/valores?periodo=2018")
    assert r.status_code == 200
    assert r.json()["total"] == 1


@pytest.mark.asyncio
async def test_valores_con_filtro_nivel_geo(client):
    """nivel_geo=nacional · filtra correctamente."""
    client._mock_db.execute.return_value = _result(rows=[])
    r = await client.get("/api/v1/indicadores/valores?nivel_geo=nacional")
    assert r.status_code == 200
    assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_valores_con_filtro_pueblo(client):
    """pueblo parcial · usa ILIKE."""
    client._mock_db.execute.return_value = _result(rows=[])
    r = await client.get("/api/v1/indicadores/valores?pueblo=arhuaco")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_valores_con_filtro_cod_indicador(client):
    """cod_indicador exacto."""
    client._mock_db.execute.return_value = _result(rows=[])
    r = await client.get("/api/v1/indicadores/valores?cod_indicador=IND-01")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_valores_n_min_filtro(client):
    """n_min personalizado (borde: 0)."""
    client._mock_db.execute.return_value = _result(rows=[])
    r = await client.get("/api/v1/indicadores/valores?n_min=0")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_valores_todos_filtros(client):
    """Todos los filtros a la vez."""
    client._mock_db.execute.return_value = _result(rows=[])
    r = await client.get(
        "/api/v1/indicadores/valores?periodo=2018&nivel_geo=pueblo&pueblo=wayuu&cod_indicador=IND-01&n_min=30"
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_valores_500(client):
    """DB error → 500."""
    client._mock_db.execute.side_effect = Exception("DB error")
    r = await client.get("/api/v1/indicadores/valores")
    assert r.status_code == 500
    assert "Error consultando valores" in r.json()["detail"]


# ---------------------------------------------------------------------------
# GET /api/v1/indicadores/serie-tiempo/{cod_indicador}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_serie_tiempo_200(client):
    """Indicador existente · devuelve serie con datos."""
    defn_row = {
        "codigo": "IND-01", "nombre": "Tasa prevalencia",
        "grupo": "salud", "formula": "disc/total*1000",
        "meta": None, "unidad": "x1000",
    }
    serie_rows = [
        {"periodo": "2005", "nivel_geo": "nacional", "cod_geo": None,
         "nombre_geo": None, "pueblo": None, "valor": 70.1,
         "numerador": 800, "denominador": 11400},
        {"periodo": "2018", "nivel_geo": "nacional", "cod_geo": None,
         "nombre_geo": None, "pueblo": None, "valor": 85.3,
         "numerador": 1000, "denominador": 11730},
    ]

    call_count = 0

    async def side_effect(query, params=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # primera llamada: definicion
            return _result(first_row=defn_row)
        else:
            # segunda llamada: serie de valores
            return _result(rows=serie_rows)

    client._mock_db.execute.side_effect = side_effect
    r = await client.get("/api/v1/indicadores/serie-tiempo/IND-01")
    assert r.status_code == 200
    body = r.json()
    assert body["indicador"]["codigo"] == "IND-01"
    assert body["total_periodos"] == 2
    assert len(body["serie"]) == 2


@pytest.mark.asyncio
async def test_serie_tiempo_404(client):
    """Indicador inexistente → 404."""
    # primera llamada devuelve None (indicador no encontrado)
    client._mock_db.execute.return_value = _result(first_row=None)
    # Asegurar que first() devuelve None
    client._mock_db.execute.return_value.first.return_value = None

    r = await client.get("/api/v1/indicadores/serie-tiempo/NO-EXISTE")
    assert r.status_code == 404
    assert "NO-EXISTE" in r.json()["detail"]


@pytest.mark.asyncio
async def test_serie_tiempo_con_filtros(client):
    """Serie con nivel_geo + cod_geo + pueblo."""
    defn_row = {
        "codigo": "IND-02", "nombre": "Brecha",
        "grupo": "social", "formula": "...",
        "meta": None, "unidad": "pct",
    }
    call_count = 0

    async def side_effect(query, params=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _result(first_row=defn_row)
        return _result(rows=[])

    client._mock_db.execute.side_effect = side_effect
    r = await client.get(
        "/api/v1/indicadores/serie-tiempo/IND-02?nivel_geo=pueblo&cod_geo=12&pueblo=wayuu"
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total_periodos"] == 0


@pytest.mark.asyncio
async def test_serie_tiempo_500(client):
    """Error inesperado → 500."""
    client._mock_db.execute.side_effect = Exception("conn error")
    r = await client.get("/api/v1/indicadores/serie-tiempo/IND-01")
    assert r.status_code == 500
    assert "Error consultando serie" in r.json()["detail"]


# ---------------------------------------------------------------------------
# POST /api/v1/indicadores/recalcular
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_recalcular_ok(client):
    """Recalcula periodo 2018 · devuelve n_generados."""
    first_row = {"n_generados": 64}
    client._mock_db.execute.return_value = _result(first_row=first_row)
    r = await client.post("/api/v1/indicadores/recalcular?periodo=2018")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["periodo"] == "2018"
    assert body["indicadores_generados"] == 64


@pytest.mark.asyncio
async def test_recalcular_default_periodo(client):
    """Sin periodo explicito usa '2018' por defecto."""
    client._mock_db.execute.return_value = _result(first_row={"n_generados": 10})
    r = await client.post("/api/v1/indicadores/recalcular")
    assert r.status_code == 200
    assert r.json()["periodo"] == "2018"


@pytest.mark.asyncio
async def test_recalcular_periodo_custom(client):
    """Periodo 2023 personalizado."""
    client._mock_db.execute.return_value = _result(first_row={"n_generados": 5})
    r = await client.post("/api/v1/indicadores/recalcular?periodo=2023")
    assert r.status_code == 200
    assert r.json()["periodo"] == "2023"


@pytest.mark.asyncio
async def test_recalcular_row_none(client):
    """Si la SP devuelve None en el result → n=0 · commit igual."""
    result_mock = MagicMock()
    result_mock.first.return_value = None
    client._mock_db.execute.return_value = result_mock
    r = await client.post("/api/v1/indicadores/recalcular?periodo=2018")
    assert r.status_code == 200
    assert r.json()["indicadores_generados"] == 0


@pytest.mark.asyncio
async def test_recalcular_500(client):
    """DB error → 500 + rollback."""
    client._mock_db.execute.side_effect = Exception("DB crash")
    r = await client.post("/api/v1/indicadores/recalcular?periodo=2018")
    assert r.status_code == 500
    assert "Error recalculando" in r.json()["detail"]


# ---------------------------------------------------------------------------
# RBAC: sin token → 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_indicadores_sin_token_401():
    """Sin override de get_current_user → 401 (auth real activa)."""
    # Usamos la app sin overrides para que falle auth
    app.dependency_overrides.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get("/api/v1/indicadores/")
    assert r.status_code == 401
