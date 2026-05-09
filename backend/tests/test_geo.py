"""
Tests unitarios para backend/app/routers/geo.py
Cobertura objetivo: >= 60% líneas

Estrategia: mock completo de get_db y get_current_user.
Endpoints públicos (departamentos, municipios, macrorregiones, smt/macrorregiones,
smt/comunidades) no requieren auth override.
Endpoints con auth (resguardos, smt/resguardos) requieren get_current_user override.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport


# ── helpers ───────────────────────────────────────────────────────────────────


def _make_row_mapping(**kwargs):
    """Fila con ._mapping directo como dict."""
    m = MagicMock()
    m._mapping = kwargs
    return m


def _make_mappings_result(rows_as_dicts: list[dict]):
    """Resultado cuyo .mappings() devuelve lista de dicts proxy."""
    proxies = []
    for d in rows_as_dicts:
        p = MagicMock()
        p.__getitem__ = lambda self, k, _d=d: _d[k]
        p.keys = lambda _d=d: _d.keys()
        for k, v in d.items():
            setattr(p, k, v)
            type(p).__getitem__ = lambda self, k, _d=d: _d[k]
        proxies.append(p)

    rows = [_make_row_from_dict(d) for d in rows_as_dicts]
    result = MagicMock()
    result.all.return_value = rows
    result.__iter__ = MagicMock(return_value=iter(rows))
    result.mappings.return_value = proxies
    result.fetchall.return_value = []
    result.first.return_value = None
    return result


def _make_row_from_dict(d: dict):
    r = MagicMock()
    r._mapping = d
    return r


def _fake_db(side_effects: list):
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=side_effects)
    return db


def _fake_user():
    u = MagicMock()
    u.id = 1
    u.username = "test_user"
    u.activo = True
    return u


# ── departamentos_geojson ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_departamentos_geojson_sin_prevalencia():
    """GET /geo/departamentos retorna FeatureCollection válida."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    rows = [
        _make_row_from_dict({"cod_dpto": "05", "nom_dpto": "Antioquia", "area_km2": 63612.0, "geometry": {"type": "Polygon", "coordinates": []}}),
    ]
    result = MagicMock()
    result.all.return_value = rows

    db = _fake_db([result])

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/departamentos")
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "FeatureCollection"
        assert isinstance(data["features"], list)
        assert len(data["features"]) == 1
        feat = data["features"][0]
        assert feat["type"] == "Feature"
        assert "properties" in feat
        assert feat["properties"]["cod_dpto"] == "05"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_departamentos_geojson_con_prevalencia():
    """GET /geo/departamentos?incluir_prevalencia=true trae campos extra."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    rows = [
        _make_row_from_dict({
            "cod_dpto": "05", "nom_dpto": "Antioquia", "area_km2": 63612.0,
            "geometry": {"type": "Polygon", "coordinates": []},
            "pob_total": 1000, "pob_disc": 100, "tasa_x_1000": 100.0, "prevalencia_pct": 10.0,
        }),
    ]
    result = MagicMock()
    result.all.return_value = rows

    db = _fake_db([result])

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/departamentos", params={"incluir_prevalencia": "true"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "FeatureCollection"
        props = data["features"][0]["properties"]
        assert "tasa_x_1000" in props
        assert "prevalencia_pct" in props
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_departamentos_geojson_vacio():
    """GET /geo/departamentos sin filas retorna features vacíos."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    result = MagicMock()
    result.all.return_value = []
    db = _fake_db([result])

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/departamentos")
        assert resp.status_code == 200
        assert resp.json()["features"] == []
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_departamentos_geojson_db_error():
    """GET /geo/departamentos con DB error → 500."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=Exception("DB down"))

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/departamentos")
        assert resp.status_code == 500
    finally:
        app.dependency_overrides.clear()


# ── municipios_geojson ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_municipios_geojson_sin_filtro():
    """GET /geo/municipios sin filtro retorna FeatureCollection."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    rows = [
        _make_row_from_dict({
            "cod_mpio": "05001", "cod_dpto": "05", "nom_mpio": "Medellin",
            "area_km2": 380.0, "geometry": {"type": "Polygon", "coordinates": []},
        }),
    ]
    result = MagicMock()
    result.all.return_value = rows
    db = _fake_db([result])

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/municipios")
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_municipios_geojson_con_filtro_dpto():
    """GET /geo/municipios?cod_dpto=05 aplica filtro."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    rows = [
        _make_row_from_dict({
            "cod_mpio": "05001", "cod_dpto": "05", "nom_mpio": "Medellin",
            "area_km2": 380.0, "geometry": None,
        }),
    ]
    result = MagicMock()
    result.all.return_value = rows
    db = _fake_db([result])

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/municipios", params={"cod_dpto": "05"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "FeatureCollection"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_municipios_geojson_db_error():
    """GET /geo/municipios con DB error → 500."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=Exception("Timeout"))

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/municipios")
        assert resp.status_code == 500
    finally:
        app.dependency_overrides.clear()


# ── listar_resguardos ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_listar_resguardos_happy_path():
    """GET /geo/resguardos retorna lista de resguardos."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    rows = [_make_row_from_dict({
        "cod_resguardo": "R001", "nombre": "Resguardo Wayuu",
        "nom_departamento": "La Guajira", "nom_municipio": "Riohacha", "poblacion_proy": 5000,
    })]
    result = MagicMock()
    result.all.return_value = rows
    result.__iter__ = MagicMock(return_value=iter(rows))

    db_mock = AsyncMock()
    db_mock.execute = AsyncMock(return_value=result)

    async def override_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/geo/resguardos",
                headers={"Authorization": "Bearer fake_token"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert isinstance(data["data"], list)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_listar_resguardos_con_filtro_mpio():
    """GET /geo/resguardos?cod_mpio=05001 aplica filtro."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    rows = [_make_row_from_dict({
        "cod_resguardo": "R002", "nombre": "Resguardo Test",
        "nom_departamento": "Antioquia", "nom_municipio": "Medellin", "poblacion_proy": 200,
    })]
    result = MagicMock()
    result.all.return_value = rows
    result.__iter__ = MagicMock(return_value=iter(rows))

    db_mock = AsyncMock()
    db_mock.execute = AsyncMock(return_value=result)

    async def override_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/geo/resguardos",
                params={"cod_mpio": "05001"},
                headers={"Authorization": "Bearer fake_token"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_listar_resguardos_sin_token():
    """GET /geo/resguardos sin Authorization → 401."""
    from app.main import app
    from app.database import get_db

    db_mock = AsyncMock()

    async def override_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_db
    # No override de get_current_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/resguardos")
        assert resp.status_code == 401
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_listar_resguardos_db_error():
    """GET /geo/resguardos con DB error → 500."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    db_mock = AsyncMock()
    db_mock.execute = AsyncMock(side_effect=Exception("DB unavailable"))

    async def override_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/resguardos", headers={"Authorization": "Bearer fake_token"})
        assert resp.status_code == 500
    finally:
        app.dependency_overrides.clear()


# ── listar_macrorregiones ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_listar_macrorregiones_happy_path():
    """GET /geo/macrorregiones retorna 5 macrorregiones."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    rows = [
        _make_row_from_dict({"id": i, "macro": f"Macro{i}", "municipios": 10*i,
                             "resguardos": 5*i, "pueblos": 3*i, "departamentos": 2})
        for i in range(1, 6)
    ]
    result = MagicMock()
    result.all.return_value = rows
    result.__iter__ = MagicMock(return_value=iter(rows))

    db_mock = AsyncMock()
    db_mock.execute = AsyncMock(return_value=result)

    async def override_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/macrorregiones")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert isinstance(data["data"], list)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_listar_macrorregiones_db_error():
    """GET /geo/macrorregiones con DB error → 500."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    db_mock = AsyncMock()
    db_mock.execute = AsyncMock(side_effect=Exception("DB error"))

    async def override_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/macrorregiones")
        assert resp.status_code == 500
    finally:
        app.dependency_overrides.clear()


# ── get_macrorregiones (smt/macrorregiones) ───────────────────────────────────

@pytest.mark.asyncio
async def test_smt_macrorregiones_happy_path():
    """GET /geo/smt/macrorregiones retorna GeoJSON FeatureCollection."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    geojson_val = {"type": "MultiPolygon", "coordinates": []}
    proxy = MagicMock()
    proxy.__getitem__ = lambda self, k: {"macro": "Amazonia", "geojson": geojson_val}[k]

    result = MagicMock()
    result.mappings.return_value = [proxy]

    db_mock = AsyncMock()
    db_mock.execute = AsyncMock(return_value=result)

    async def override_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/smt/macrorregiones")
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 1
        assert data["features"][0]["properties"]["macro"] == "Amazonia"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_smt_macrorregiones_sin_geojson():
    """GET /geo/smt/macrorregiones omite features con geojson null."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    proxy = MagicMock()
    proxy.__getitem__ = lambda self, k: {"macro": "SinGeo", "geojson": None}[k]

    result = MagicMock()
    result.mappings.return_value = [proxy]

    db_mock = AsyncMock()
    db_mock.execute = AsyncMock(return_value=result)

    async def override_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/smt/macrorregiones")
        assert resp.status_code == 200
        data = resp.json()
        # Feature omitida porque geojson es None
        assert len(data["features"]) == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_smt_macrorregiones_db_error():
    """GET /geo/smt/macrorregiones con DB error → 500."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    db_mock = AsyncMock()
    db_mock.execute = AsyncMock(side_effect=Exception("Connection refused"))

    async def override_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/smt/macrorregiones")
        assert resp.status_code == 500
    finally:
        app.dependency_overrides.clear()


# ── get_resguardos_geo (smt/resguardos) ──────────────────────────────────────

def _resguardo_proxy(with_geo=True):
    # Keys must match the SQL aliases used in get_resguardos_geo
    d = {
        "territorio": "Resguardo Test",
        "pueblo_onic": "Wayuu",
        "dpto_cnmbr": "La Guajira",
        "mpio_cnmbr": "Riohacha",
        "mpio_cdpmp": "44001",
        "ccdgo_terr": "R001",
        "org_regnal": "CIT",
        "area_pg_ha": 50000.5,
        "tasa_prevalencia": 100.0,
        "con_cap_diversas": 50,   # alias: COALESCE(d.con_disc,0) AS con_cap_diversas
        "poblacion": 500,          # alias: COALESCE(d.pob_indigena,0) AS poblacion
        "fuente_dato": "municipal",
        "geojson": {"type": "MultiPolygon", "coordinates": []} if with_geo else None,
    }
    proxy = MagicMock()
    proxy.__getitem__ = lambda self, k, _d=d: _d[k]
    return proxy


@pytest.mark.asyncio
async def test_smt_resguardos_happy_path():
    """GET /geo/smt/resguardos retorna FeatureCollection con propiedades."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    result = MagicMock()
    result.mappings.return_value = [_resguardo_proxy(with_geo=True)]

    db_mock = AsyncMock()
    db_mock.execute = AsyncMock(return_value=result)

    async def override_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/smt/resguardos", headers={"Authorization": "Bearer fake_token"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 1
        props = data["features"][0]["properties"]
        assert "territorio" in props
        assert "tasa_prevalencia" in props
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_smt_resguardos_omite_sin_geo():
    """GET /geo/smt/resguardos omite resguardos con geojson null."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    result = MagicMock()
    result.mappings.return_value = [_resguardo_proxy(with_geo=False)]

    db_mock = AsyncMock()
    db_mock.execute = AsyncMock(return_value=result)

    async def override_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/smt/resguardos", headers={"Authorization": "Bearer fake_token"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["features"]) == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_smt_resguardos_sin_token():
    """GET /geo/smt/resguardos sin Authorization → 401."""
    from app.main import app
    from app.database import get_db

    db_mock = AsyncMock()

    async def override_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_db

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/smt/resguardos")
        assert resp.status_code == 401
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_smt_resguardos_db_error():
    """GET /geo/smt/resguardos con DB error → 500."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    db_mock = AsyncMock()
    db_mock.execute = AsyncMock(side_effect=Exception("DB down"))

    async def override_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/smt/resguardos", headers={"Authorization": "Bearer fake_token"})
        assert resp.status_code == 500
    finally:
        app.dependency_overrides.clear()


# ── get_comunidades_geo (smt/comunidades) ────────────────────────────────────

def _comunidad_proxy(dpto_ccdgo="05"):
    d = {
        "comun_cnmbr": "Comunidad Test", "pueblo_onic": "Embera", "dpto_cnmbr": "Antioquia",
        "mpio_cnmbr": "Medellin", "mpio_cdpmp": "05001", "personas": 120, "viviendas": 30,
        "geojson": {"type": "Point", "coordinates": [-75.5, 6.2]},
    }
    proxy = MagicMock()
    proxy.__getitem__ = lambda self, k, _d=d: _d[k]
    return proxy


@pytest.mark.asyncio
async def test_smt_comunidades_happy_path():
    """GET /geo/smt/comunidades retorna FeatureCollection de puntos."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    result = MagicMock()
    result.mappings.return_value = [_comunidad_proxy()]

    db_mock = AsyncMock()
    db_mock.execute = AsyncMock(return_value=result)

    async def override_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/smt/comunidades")
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 1
        props = data["features"][0]["properties"]
        assert "nombre" in props
        assert "pueblo" in props
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_smt_comunidades_con_filtro_dpto():
    """GET /geo/smt/comunidades?cod_dpto=05 aplica filtro."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    result = MagicMock()
    result.mappings.return_value = [_comunidad_proxy()]

    db_mock = AsyncMock()
    db_mock.execute = AsyncMock(return_value=result)

    async def override_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/smt/comunidades", params={"cod_dpto": "05"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "FeatureCollection"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_smt_comunidades_omite_sin_geo():
    """GET /geo/smt/comunidades omite features con geojson null."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    null_proxy = MagicMock()
    null_proxy.__getitem__ = lambda self, k: None if k == "geojson" else "x"

    result = MagicMock()
    result.mappings.return_value = [null_proxy]

    db_mock = AsyncMock()
    db_mock.execute = AsyncMock(return_value=result)

    async def override_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/smt/comunidades")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["features"]) == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_smt_comunidades_db_error():
    """GET /geo/smt/comunidades con DB error → 500."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    db_mock = AsyncMock()
    db_mock.execute = AsyncMock(side_effect=Exception("Connection reset"))

    async def override_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/geo/smt/comunidades")
        assert resp.status_code == 500
    finally:
        app.dependency_overrides.clear()
