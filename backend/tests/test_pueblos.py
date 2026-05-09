"""
Tests unitarios para backend/app/routers/pueblos.py
Cobertura objetivo: >= 60% líneas

Estrategia: mock completo de get_db (AsyncSession) y get_current_user.
No requiere Postgres activo.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

# ── fixtures compartidos ──────────────────────────────────────────────────────


def _make_row(*values, keys=None):
    """Crea un objeto que simula una fila SQLAlchemy con ._mapping."""
    m = MagicMock()
    if keys:
        m._mapping = dict(zip(keys, values))
    else:
        m._mapping = {}
    return m


def _make_result(rows):
    """Crea un resultado async que devuelve filas.
    El router itera directo sobre el result: `for r in result` AND `result.all()`.
    """
    result = MagicMock()
    result.all.return_value = rows
    result.fetchall.return_value = rows
    result.first.return_value = rows[0] if rows else None
    # Make directly iterable (for r in result)
    result.__iter__ = MagicMock(return_value=iter(rows))
    return result


def _make_db(side_effects: list):
    """Crea un AsyncSession mock con execute devolviendo resultados en orden."""
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=side_effects)
    return db


def _fake_user():
    u = MagicMock()
    u.id = 1
    u.username = "test_user"
    u.activo = True
    return u


# ── keys de las tablas principales ───────────────────────────────────────────
DISC_KEYS = [
    "cod_pueblo", "pueblo", "con_discapacidad", "sin_discapacidad",
    "total", "prevalencia_pct", "tasa_x_1000", "confiabilidad",
]


# ── listar_pueblos ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_listar_pueblos_happy_path():
    """GET /pueblos/ sin filtros retorna lista y metadata."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    row = _make_row("001", "Wayuu", 100, 900, 1000, 10.0, 100.0, "ALTA", keys=DISC_KEYS)
    result = _make_result([row])
    db = _make_db([result])

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/pueblos/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert isinstance(data["data"], list)
        assert data["data"][0]["cod_pueblo"] == "001"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_listar_pueblos_lista_vacia():
    """GET /pueblos/ con período sin datos retorna total=0."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    result = _make_result([])
    db = _make_db([result])

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/pueblos/", params={"periodo": "2005"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["data"] == []
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_listar_pueblos_sin_token():
    """GET /pueblos/ sin Authorization → 401."""
    from app.main import app
    from app.database import get_db

    db = _make_db([])

    async def override_db():
        yield db

    # Solo sobreescribimos DB, NO get_current_user → lanza 401
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides.pop("get_current_user", None)

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/pueblos/")
        assert resp.status_code == 401
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_listar_pueblos_filtro_cod_mpio():
    """GET /pueblos/?cod_mpio=05001 aplica filtro geográfico por municipio."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    # Primera query: resolver cod_pueblos del mpio
    filtro_row = MagicMock()
    filtro_row.__getitem__ = lambda self, i: "001"
    filtro_result = MagicMock()
    filtro_result.fetchall.return_value = [(("001",))]

    row = _make_row("001", "Wayuu", 100, 900, 1000, 10.0, 100.0, "ALTA", keys=DISC_KEYS)
    main_result = _make_result([row])

    db = _make_db([filtro_result, main_result])

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/pueblos/", params={"cod_mpio": "05001"})
        assert resp.status_code == 200
        data = resp.json()
        assert "filtro_aplicado" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_listar_pueblos_filtro_cod_mpio_sin_pueblos():
    """GET /pueblos/?cod_mpio=XXXXX retorna total=0 cuando no hay pueblos en municipio."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    # Query filtro no devuelve pueblos
    filtro_result = MagicMock()
    filtro_result.fetchall.return_value = []

    db = _make_db([filtro_result])

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/pueblos/", params={"cod_mpio": "99999"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["data"] == []
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_listar_pueblos_filtro_cod_dpto():
    """GET /pueblos/?cod_dpto=05 aplica filtro por departamento."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    filtro_result = MagicMock()
    filtro_result.fetchall.return_value = [("001",)]

    row = _make_row("001", "Wayuu", 100, 900, 1000, 10.0, 100.0, "ALTA", keys=DISC_KEYS)
    main_result = _make_result([row])

    db = _make_db([filtro_result, main_result])

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/pueblos/", params={"cod_dpto": "05"})
        assert resp.status_code == 200
        data = resp.json()
        assert "filtro_aplicado" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_listar_pueblos_filtro_cod_macro():
    """GET /pueblos/?cod_macro=Amazonia aplica filtro por macrorregión."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    filtro_result = MagicMock()
    filtro_result.fetchall.return_value = [("001",), ("002",)]

    row1 = _make_row("001", "Tikuna", 50, 450, 500, 10.0, 100.0, "ALTA", keys=DISC_KEYS)
    row2 = _make_row("002", "Huitoto", 30, 270, 300, 10.0, 100.0, "MEDIA", keys=DISC_KEYS)
    main_result = _make_result([row1, row2])

    db = _make_db([filtro_result, main_result])

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/pueblos/", params={"cod_macro": "Amazonia"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert "filtro_aplicado" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_listar_pueblos_db_error():
    """GET /pueblos/ cuando DB lanza excepción → 500."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=Exception("DB connection error"))

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/pueblos/")
        assert resp.status_code == 500
    finally:
        app.dependency_overrides.clear()


# ── perfil_pueblo ─────────────────────────────────────────────────────────────

PREV_KEYS = DISC_KEYS  # mismas columnas


def _perfil_db():
    """DB mock con todos los datos para perfil completo."""
    prev_row = _make_row("001", "Wayuu", 100, 900, 1000, 10.0, 100.0, "ALTA", keys=PREV_KEYS)
    prev_result = _make_result([prev_row])

    sexo_keys = ["hombres", "mujeres", "total"]
    sexo_row = _make_row(480, 520, 1000, keys=sexo_keys)
    sexo_result = _make_result([sexo_row])

    edad_keys = ["grupo_edad", "valor"]
    edad_row = _make_row("0-4", 50, keys=edad_keys)
    edad_result = _make_result([edad_row])

    lim_keys = ["limitacion", "valor"]
    lim_row = _make_row("Vision", 30, keys=lim_keys)
    lim_result = _make_result([lim_row])

    trat_keys = ["tratamiento", "valor"]
    trat_row = _make_row("Medico", 20, keys=trat_keys)
    trat_result = _make_result([trat_row])

    causa_keys = ["causa", "valor"]
    causa_row = _make_row("Enfermedad", 40, keys=causa_keys)
    causa_result = _make_result([causa_row])

    enf_keys = ["enfermo_si", "enfermo_no", "no_informa", "total"]
    enf_row = _make_row(10, 85, 5, 100, keys=enf_keys)
    enf_result = _make_result([enf_row])

    return _make_db([prev_result, sexo_result, edad_result, lim_result, trat_result, causa_result, enf_result])


@pytest.mark.asyncio
async def test_perfil_pueblo_happy_path():
    """GET /pueblos/{cod}/perfil retorna todas las secciones."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    db = _perfil_db()

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/pueblos/001/perfil")
        assert resp.status_code == 200
        data = resp.json()
        assert "prevalencia" in data
        assert "sexo" in data
        assert "piramide_edad" in data
        assert "limitaciones" in data
        assert "tratamiento" in data
        assert "causas" in data
        assert "enfermedad" in data
        assert "confiabilidad" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_perfil_pueblo_404_no_existe():
    """GET /pueblos/ZZZ/perfil cuando el pueblo no existe → 404."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    # prev_result sin filas → .first() devuelve None
    prev_result = _make_result([])
    db = _make_db([prev_result])

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/pueblos/ZZZ/perfil")
        assert resp.status_code == 404
        detail = resp.json()["detail"]
        assert "ZZZ" in detail
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_perfil_pueblo_confiabilidad_baja_n_menor_30():
    """Pueblo con total < 30 → confiabilidad = BAJA aunque la BD diga MEDIA."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    prev_row = _make_row("002", "Pequeno", 2, 18, 20, 10.0, 100.0, "MEDIA", keys=PREV_KEYS)
    prev_result = _make_result([prev_row])

    # Resto de queries devuelven vacío
    db = _make_db([prev_result] + [_make_result([]) for _ in range(6)])

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/pueblos/002/perfil")
        assert resp.status_code == 200
        assert resp.json()["confiabilidad"] == "BAJA"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_perfil_pueblo_db_error():
    """GET /pueblos/{cod}/perfil con DB error → 500."""
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
            resp = await client.get("/api/v1/pueblos/001/perfil")
        assert resp.status_code == 500
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_perfil_pueblo_sin_token():
    """GET /pueblos/{cod}/perfil sin token → 401."""
    from app.main import app
    from app.database import get_db

    db = _make_db([])

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides.pop("get_current_user", None)

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/pueblos/001/perfil")
        assert resp.status_code == 401
    finally:
        app.dependency_overrides.clear()


# ── territorios_pueblo ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_territorios_pueblo_happy_path():
    """GET /pueblos/{cod}/territorios retorna lista de dptos."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    check_keys = ["pueblo"]
    check_row = _make_row("Wayuu", keys=check_keys)
    check_result = _make_result([check_row])

    terr_keys = ["cod_dpto", "nom_dpto", "pueblo", "con_discapacidad",
                 "sin_discapacidad", "total", "tasa_x_1000", "confiabilidad"]
    terr_row = _make_row("05", "Antioquia", "Wayuu", 10, 90, 100, 100.0, "CONFIABLE", keys=terr_keys)
    terr_result = _make_result([terr_row])

    db = _make_db([check_result, terr_result])

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/pueblos/001/territorios")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert isinstance(data["data"], list)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_territorios_pueblo_404():
    """GET /pueblos/ZZZ/territorios → 404 cuando pueblo no existe."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    check_result = _make_result([])  # primer check devuelve vacío → 404
    db = _make_db([check_result])

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/pueblos/ZZZ/territorios")
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_territorios_pueblo_db_error():
    """GET /pueblos/{cod}/territorios con DB error → 500."""
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
            resp = await client.get("/api/v1/pueblos/001/territorios")
        assert resp.status_code == 500
    finally:
        app.dependency_overrides.clear()


# ── pueblos_en_municipio ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pueblos_en_municipio_happy_path():
    """GET /pueblos/por-municipio/05001 retorna pueblos con datos."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    pm_keys = ["cod_pueblo", "pueblo", "poblacion", "pct_en_mpio", "es_dominante", "nom_mpio"]
    row = _make_row("001", "Wayuu", 500, 25.0, True, "Medellin", keys=pm_keys)
    result = _make_result([row])
    db = _make_db([result])

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/pueblos/por-municipio/05001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["cod_mpio"] == "05001"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_pueblos_en_municipio_404():
    """GET /pueblos/por-municipio/XXXXX → 404 cuando no hay pueblos."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    result = _make_result([])
    db = _make_db([result])

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/pueblos/por-municipio/99999")
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_pueblos_en_municipio_db_error():
    """GET /pueblos/por-municipio/{cod} con DB error → 500."""
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=Exception("DB connection lost"))

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/pueblos/por-municipio/05001")
        assert resp.status_code == 500
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_pueblos_en_municipio_sin_token():
    """GET /pueblos/por-municipio/{cod} sin token → 401."""
    from app.main import app
    from app.database import get_db

    db = _make_db([])

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides.pop("get_current_user", None)

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/pueblos/por-municipio/05001")
        assert resp.status_code == 401
    finally:
        app.dependency_overrides.clear()
