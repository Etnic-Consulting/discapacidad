"""
conftest.py raíz del backend.

Se ejecuta en la fase de configuración de pytest (pytest_configure), ANTES
de que cualquier módulo de test sea importado.

Resuelve dos problemas cuando pytest se lanza desde el repo raíz
(copia github/) en lugar de desde backend/:

1. sys.path no incluye backend/ → `from app.xxx import ...` falla con
   ModuleNotFoundError.

2. pydantic-settings carga el .env del cwd (repo raíz), que tiene campos
   extra (github_token, groq_api_key, etc.) no declarados en Settings →
   ValidationError con extra='forbid'.

Solución:
- Añadir backend/ a sys.path.
- Patch the pydantic-settings BaseSettings so that Settings() usa
  env_file apuntando al backend/.env (solo campos válidos) y extra='ignore'.
"""
import os
import sys


def pytest_configure(config):
    """Hook ejecutado por pytest antes de la colección de tests."""
    backend_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. sys.path: necesario cuando cwd != backend/
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    # 2. Patch Settings ANTES de que app.config sea importado.
    #    Reemplaza la clase en app.config con una que ignora campos extra
    #    y apunta env_file al backend/.env (sin campos extra).
    local_env = os.path.join(backend_dir, ".env")

    # Importar pydantic-settings ahora para poder subclasificar
    from pydantic_settings import BaseSettings

    class _PatchedSettings(BaseSettings):
        database_url: str = (
            "postgresql+asyncpg://smt_admin:smt_onic_2026@localhost:5450/smt_onic"
        )
        database_url_sync: str = (
            "postgresql://smt_admin:smt_onic_2026@localhost:5450/smt_onic"
        )
        cors_origins: list[str] = [
            "http://localhost:3000",
            "http://localhost:5173",
        ]

        class Config:
            extra = "ignore"          # ignorar campos extra del .env raíz
            env_file = local_env      # apuntar al backend/.env limpio

    # Inyectar en app.config antes de que el módulo sea importado
    import importlib
    import types

    # Crear módulo ficticio con settings ya parcheado
    fake_config = types.ModuleType("app.config")
    fake_config.settings = _PatchedSettings()
    sys.modules["app.config"] = fake_config
