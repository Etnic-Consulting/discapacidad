"""
V06 · Tests cobertura >= 55% para backend/app/routers/conflicto.py

Todos los endpoints dependen de AsyncSession (PostgreSQL).
Estrategia: override de la dependencia get_db con un mock async.
No se hacen llamadas reales a BD.
"""
from __future__ import annotations

import os
import sys
import types
import unittest.mock as mock
from pathlib import Path
from typing import AsyncGenerator

import pytest

# Asegurar que 'backend/' está en sys.path
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# ── Inyectar módulos stub ANTES de que cualquier import de app los cargue ──────
# app.config.Settings intenta leer .env del CWD (que tiene campos extra → ValidationError).
# Sustituimos app.config y app.database con stubs que no tocan pydantic_settings ni SQLAlchemy.

_stub_config = types.ModuleType("app.config")

class _FakeSettings:
    database_url = "postgresql+asyncpg://test:test@localhost:5450/test"
    database_url_sync = "postgresql://test:test@localhost:5450/test"
    cors_origins: list = []

_stub_config.settings = _FakeSettings()
_stub_config.Settings = _FakeSettings
sys.modules.setdefault("app.config", _stub_config)

_stub_database = types.ModuleType("app.database")

async def _stub_get_db():  # placeholder; siempre se sobreescribe con dependency_overrides
    raise RuntimeError("get_db stub: usa dependency_overrides en el test")
    yield  # hace que sea un async generator

_stub_database.get_db = _stub_get_db
# Stub de engines para que ningún módulo falle al importar app.database
_stub_database.async_engine = None
_stub_database.sync_engine = None
_stub_database.async_session = None
sys.modules.setdefault("app.database", _stub_database)

# Stub de app.filters (usa app.database internamente)
_stub_filters = types.ModuleType("app.filters")
from dataclasses import dataclass, field as dc_field

@dataclass
class _FakeFiltro:
    cod_macro: str | None = None
    cod_dpto: str | None = None
    cod_mpio: str | None = None
    cod_pueblo: str | None = None
    cod_resguardo: str | None = None
    mpios: list = dc_field(default_factory=list)
    dptos: list = dc_field(default_factory=list)

async def _stub_resolver_filtros(db, cod_macro=None, cod_dpto=None, cod_mpio=None, cod_pueblo=None, cod_resguardo=None):
    f = _FakeFiltro(cod_macro=cod_macro, cod_dpto=cod_dpto, cod_mpio=cod_mpio,
                    cod_pueblo=cod_pueblo, cod_resguardo=cod_resguardo)
    if cod_mpio:
        f.mpios = [cod_mpio]
        f.dptos = [cod_mpio[:2]]
    elif cod_dpto:
        f.dptos = [cod_dpto]
    return f

_stub_filters.resolver_filtros = _stub_resolver_filtros
_stub_filters.FiltroGeografico = _FakeFiltro
sys.modules.setdefault("app.filters", _stub_filters)

from fastapi import FastAPI
from fastapi.testclient import TestClient

# ─── Mock de SQLAlchemy async ─────────────────────────────────────────────────

class _FakeRow:
    """Row fake que soporta ._mapping."""
    def __init__(self, data: dict):
        self._mapping = data


class _FakeResult:
    """Resultado fake de db.execute()."""
    def __init__(self, rows: list[dict]):
        self._rows = [_FakeRow(r) for r in rows]

    def __iter__(self):
        return iter(self._rows)

    def fetchall(self):
        return [(list(r._mapping.values())[0],) for r in self._rows]


class _FakeDB:
    """AsyncSession fake con respuesta configurable."""
    def __init__(self, rows: list[dict] | None = None, raise_exc: Exception | None = None):
        self._rows = rows or []
        self._raise_exc = raise_exc

    async def execute(self, query, params=None):
        if self._raise_exc:
            raise self._raise_exc
        return _FakeResult(self._rows)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


def make_app(db_rows: list[dict] | None = None, raise_exc: Exception | None = None):
    """Crea app FastAPI con get_db override."""
    from app.routers import conflicto

    app = FastAPI()
    app.include_router(conflicto.router, prefix="/api/v1/conflicto")

    fake_db = _FakeDB(db_rows, raise_exc)

    async def override_get_db():
        yield fake_db

    # get_db que importa conflicto.py es el de app.database (stub)
    app.dependency_overrides[_stub_get_db] = override_get_db
    return app


# ─── Helpers para filtros ─────────────────────────────────────────────────────

def make_client_with_rows(rows: list[dict]):
    return TestClient(make_app(rows), raise_server_exceptions=False)


def make_client_with_error(exc: Exception):
    return TestClient(make_app(raise_exc=exc), raise_server_exceptions=False)


# ─── /victimas/resumen ───────────────────────────────────────────────────────

class TestVictimasResumen:
    def test_200_respuesta_vacia(self):
        client = make_client_with_rows([])
        r = client.get("/api/v1/conflicto/victimas/resumen")
        assert r.status_code == 200
        body = r.json()
        assert "total" in body
        assert "data" in body
        assert body["total"] == 0

    def test_200_con_datos(self):
        rows = [
            {"etnia": "Indigena", "discapacidad": "FISICA",
             "personas_ocurrencia": 100, "sujetos_atencion": 80, "total_eventos": 5},
            {"etnia": "Indigena", "discapacidad": "VISUAL",
             "personas_ocurrencia": 50, "sujetos_atencion": 40, "total_eventos": 3},
        ]
        client = make_client_with_rows(rows)
        r = client.get("/api/v1/conflicto/victimas/resumen")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 2
        assert len(body["data"]) == 2

    def test_500_en_excepcion_bd(self):
        client = make_client_with_error(RuntimeError("BD caída"))
        r = client.get("/api/v1/conflicto/victimas/resumen")
        assert r.status_code == 500
        body = r.json()
        assert "detail" in body


# ─── /victimas/hechos ─────────────────────────────────────────────────────────

class TestVictimasHechos:
    def test_200_sin_filtros(self):
        rows = [
            {"cod_dpto": "44", "estado_depto": "La Guajira",
             "cod_mpio": "44001", "ciudad_municipio": "Riohacha",
             "hecho": "Desplazamiento", "discapacidad": "FISICA",
             "personas_ocurrencia": 200, "sujetos_atencion": 180, "total_eventos": 10},
        ]
        client = make_client_with_rows(rows)
        r = client.get("/api/v1/conflicto/victimas/hechos")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert body["data"][0]["hecho"] == "Desplazamiento"

    def test_200_con_filtro_hecho(self):
        rows = [
            {"cod_dpto": "05", "estado_depto": "Antioquia",
             "cod_mpio": "05001", "ciudad_municipio": "Medellín",
             "hecho": "Homicidio", "discapacidad": "FISICA",
             "personas_ocurrencia": 10, "sujetos_atencion": 9, "total_eventos": 2},
        ]
        client = make_client_with_rows(rows)
        r = client.get("/api/v1/conflicto/victimas/hechos", params={"hecho": "Homicidio"})
        assert r.status_code == 200
        body = r.json()
        assert body["total"] >= 0

    def test_200_con_filtro_dpto(self):
        rows = [
            {"cod_dpto": "44", "estado_depto": "La Guajira",
             "cod_mpio": "44001", "ciudad_municipio": "Riohacha",
             "hecho": "Desplazamiento", "discapacidad": "SIN_INFORMACION",
             "personas_ocurrencia": 300, "sujetos_atencion": 280, "total_eventos": 15},
        ]
        client = make_client_with_rows(rows)
        r = client.get("/api/v1/conflicto/victimas/hechos", params={"cod_dpto": "44"})
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1

    def test_500_en_excepcion_bd(self):
        client = make_client_with_error(Exception("timeout"))
        r = client.get("/api/v1/conflicto/victimas/hechos")
        assert r.status_code == 500

    def test_200_sin_datos(self):
        client = make_client_with_rows([])
        r = client.get("/api/v1/conflicto/victimas/hechos")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 0
        assert body["data"] == []


# ─── /victimas/por-pueblo ─────────────────────────────────────────────────────

class TestVictimasPorPuebloRanking:
    def test_200_basico(self):
        rows = [
            {"pueblo_imputado": "Wayuu", "total_victimas": 5000,
             "fisica": 1000, "visual": 800, "auditiva": 600,
             "intelectual": 400, "psicosocial": 300, "sin_informacion": 900,
             "confianza_imputacion": "alta"},
            {"pueblo_imputado": "Nasa", "total_victimas": 2000,
             "fisica": 500, "visual": 300, "auditiva": 200,
             "intelectual": 100, "psicosocial": 150, "sin_informacion": 750,
             "confianza_imputacion": "media"},
        ]
        client = make_client_with_rows(rows)
        r = client.get("/api/v1/conflicto/victimas/por-pueblo")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 2
        assert body["total_victimas"] == 7000

    def test_200_con_limite(self):
        rows = [{"pueblo_imputado": f"Pueblo{i}", "total_victimas": 100 - i,
                 "fisica": 0, "visual": 0, "auditiva": 0,
                 "intelectual": 0, "psicosocial": 0, "sin_informacion": 100 - i,
                 "confianza_imputacion": "baja"} for i in range(5)]
        client = make_client_with_rows(rows)
        r = client.get("/api/v1/conflicto/victimas/por-pueblo", params={"limit": 5})
        assert r.status_code == 200

    def test_500_en_excepcion(self):
        client = make_client_with_error(Exception("error db"))
        r = client.get("/api/v1/conflicto/victimas/por-pueblo")
        assert r.status_code == 500

    def test_200_resultado_vacio(self):
        client = make_client_with_rows([])
        r = client.get("/api/v1/conflicto/victimas/por-pueblo")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 0
        assert body["total_victimas"] == 0

    def test_200_con_filtro_macro(self):
        rows = [{"pueblo_imputado": "Wayuu", "total_victimas": 3000,
                 "fisica": 500, "visual": 400, "auditiva": 300,
                 "intelectual": 200, "psicosocial": 100, "sin_informacion": 1500,
                 "confianza_imputacion": "alta"}]
        client = make_client_with_rows(rows)
        r = client.get("/api/v1/conflicto/victimas/por-pueblo", params={"cod_macro": "NORTE"})
        assert r.status_code == 200


# ─── /victimas/por-hecho ─────────────────────────────────────────────────────

class TestVictimasPorHecho:
    def test_200_basico(self):
        rows = [
            {"hecho": "Desplazamiento", "total_victimas": 20000,
             "fisica": 4000, "visual": 3000, "auditiva": 2000,
             "intelectual": 1000, "psicosocial": 500},
            {"hecho": "Homicidio", "total_victimas": 5000,
             "fisica": 1000, "visual": 800, "auditiva": 600,
             "intelectual": 400, "psicosocial": 200},
        ]
        client = make_client_with_rows(rows)
        r = client.get("/api/v1/conflicto/victimas/por-hecho")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 2
        assert body["total_victimas"] == 25000

    def test_200_vacio(self):
        client = make_client_with_rows([])
        r = client.get("/api/v1/conflicto/victimas/por-hecho")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 0
        assert body["total_victimas"] == 0

    def test_500_en_excepcion(self):
        client = make_client_with_error(RuntimeError("sql error"))
        r = client.get("/api/v1/conflicto/victimas/por-hecho")
        assert r.status_code == 500

    def test_200_con_filtro_mpio(self):
        rows = [{"hecho": "Minas", "total_victimas": 50,
                 "fisica": 10, "visual": 5, "auditiva": 5,
                 "intelectual": 5, "psicosocial": 5}]
        client = make_client_with_rows(rows)
        r = client.get("/api/v1/conflicto/victimas/por-hecho", params={"cod_mpio": "05001"})
        assert r.status_code == 200


# ─── /victimas/por-tipo ──────────────────────────────────────────────────────

class TestVictimasPorTipo:
    def test_200_basico(self):
        rows = [
            {"tipo": "FISICA", "total_victimas": 15000},
            {"tipo": "VISUAL", "total_victimas": 8000},
            {"tipo": "AUDITIVA", "total_victimas": 5000},
            {"tipo": "INTELECTUAL", "total_victimas": 4000},
            {"tipo": "PSICOSOCIAL", "total_victimas": 3000},
            {"tipo": "SIN_INFORMACION", "total_victimas": 2562},
        ]
        client = make_client_with_rows(rows)
        r = client.get("/api/v1/conflicto/victimas/por-tipo")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 6
        assert body["total_victimas"] == 37562

    def test_200_vacio(self):
        client = make_client_with_rows([])
        r = client.get("/api/v1/conflicto/victimas/por-tipo")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 0

    def test_500_en_excepcion(self):
        client = make_client_with_error(Exception("pg error"))
        r = client.get("/api/v1/conflicto/victimas/por-tipo")
        assert r.status_code == 500

    def test_200_con_filtro_resguardo(self):
        rows = [{"tipo": "FISICA", "total_victimas": 100}]
        client = make_client_with_rows(rows)
        r = client.get("/api/v1/conflicto/victimas/por-tipo", params={"cod_resguardo": "R001"})
        assert r.status_code == 200


# ─── /victimas/pueblo/{pueblo_id} ────────────────────────────────────────────

class TestVictimasPorPueblo:
    def test_200_por_codigo_numerico(self):
        """pueblo_id numérico → consulta resumen_pueblo_hecho."""
        rows = [
            {"cod_pueblo_imputado": "001", "pueblo_imputado": "Wayuu",
             "hecho": "Desplazamiento", "tipo_disc_limpia": "FISICA",
             "cod_dpto": "44", "cod_mpio": "44001", "cantidad": 500},
        ]
        client = make_client_with_rows(rows)
        r = client.get("/api/v1/conflicto/victimas/pueblo/001")
        assert r.status_code == 200
        body = r.json()
        assert body["cod_pueblo"] == "001"
        assert body["pueblo"] == "Wayuu"
        assert body["total"] == 1

    def test_200_por_nombre(self):
        """pueblo_id texto → consulta por ILIKE."""
        rows = [
            {"cod_pueblo_imputado": "002", "pueblo_imputado": "Nasa",
             "hecho": "Homicidio", "tipo_disc_limpia": "VISUAL",
             "cod_dpto": "19", "cod_mpio": "19001", "cantidad": 200},
        ]
        client = make_client_with_rows(rows)
        r = client.get("/api/v1/conflicto/victimas/pueblo/Nasa")
        assert r.status_code == 200
        body = r.json()
        assert body["pueblo"] == "Nasa"

    def test_404_pueblo_no_encontrado(self):
        """Cuando resumen_pueblo_hecho y ruv_pueblo están vacíos → 404."""
        client = make_client_with_rows([])
        r = client.get("/api/v1/conflicto/victimas/pueblo/9999")
        assert r.status_code == 404
        body = r.json()
        assert "detail" in body
        assert "9999" in body["detail"]

    def test_500_en_excepcion_critica(self):
        """Excepción no controlada en fallback → 500."""
        from app.routers import conflicto as conf_mod

        # Primera llamada (resumen_pueblo_hecho) falla con RuntimeError
        # Segunda llamada (imp.ruv_pueblo) también falla
        call_count = 0

        class _FailTwiceDB:
            async def execute(self, query, params=None):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise RuntimeError("primera falla")
                raise RuntimeError("segunda falla critica")

        async def override_db():
            yield _FailTwiceDB()

        from app.database import get_db
        app = FastAPI()
        app.include_router(conf_mod.router, prefix="/api/v1/conflicto")
        app.dependency_overrides[get_db] = override_db
        c = TestClient(app, raise_server_exceptions=False)
        r = c.get("/api/v1/conflicto/victimas/pueblo/123")
        assert r.status_code == 500

    def test_200_pueblo_nombre_vacio_resultado(self):
        """Primera query vacia + segunda con datos (fallback a ruv_pueblo)."""
        call_count = 0
        ruv_rows = [
            {"cod_pueblo_imputado": "003", "pueblo_imputado": "Embera",
             "hecho": "Minas", "discapacidad": "1", "sexo": "M",
             "ciclo_vital": "Adulto", "eventos": 50,
             "confianza": "alta", "metodo_imputacion": "ML"},
        ]

        class _FallbackDB:
            async def execute(self, query, params=None):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    # Primera consulta (resumen_pueblo_hecho) → vacía
                    return _FakeResult([])
                # Segunda (ruv_pueblo) → con datos
                return _FakeResult(ruv_rows)

        from app.routers import conflicto as conf_mod
        from app.database import get_db

        async def override_db():
            yield _FallbackDB()

        app = FastAPI()
        app.include_router(conf_mod.router, prefix="/api/v1/conflicto")
        app.dependency_overrides[get_db] = override_db
        c = TestClient(app, raise_server_exceptions=False)
        r = c.get("/api/v1/conflicto/victimas/pueblo/003")
        assert r.status_code == 200
        body = r.json()
        assert body["fuente"] == "imp.ruv_pueblo"
        assert body["pueblo"] == "Embera"
