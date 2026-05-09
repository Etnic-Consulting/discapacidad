"""
conftest_mock.py · Fixtures compartidos para tests mock (sin BD real).

Provee:
  - async_client: httpx.AsyncClient apuntando a la app FastAPI con deps sobreescritas.
  - mock_db: AsyncSession mockeada via AsyncMock.
  - override_auth: fixture que inyecta un usuario fake en get_current_user.
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

def make_mock_db():
    """Devuelve una AsyncSession completamente mockeada."""
    db = AsyncMock()
    # db.execute devuelve un resultado mockeado por defecto
    result = MagicMock()
    result.__iter__ = MagicMock(return_value=iter([]))
    result.first.return_value = None
    result.scalar.return_value = None
    result.fetchall.return_value = []
    db.execute.return_value = result
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


def make_fake_user():
    """Devuelve un objeto Usuario fake."""
    user = MagicMock()
    user.id = 1
    user.username = "testuser"
    user.nombre = "Test User"
    user.rol = "admin"
    user.activo = True
    return user


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    return make_mock_db()


@pytest.fixture
def fake_user():
    return make_fake_user()


@pytest_asyncio.fixture
async def async_client(mock_db, fake_user):
    """
    AsyncClient con get_db y get_current_user sobreescritos.
    El mock_db es el mismo objeto que el test puede configurar antes de llamar.
    """
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: fake_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
