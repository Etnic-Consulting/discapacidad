from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://smt_admin:smt_onic_2026@localhost:5450/smt_onic"
    database_url_sync: str = "postgresql://smt_admin:smt_onic_2026@localhost:5450/smt_onic"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ]

    class Config:
        env_file = ".env"


settings = Settings()
