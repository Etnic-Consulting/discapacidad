from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://smt_admin:smt_onic_2026@localhost:5450/smt_onic"
    database_url_sync: str = "postgresql://smt_admin:smt_onic_2026@localhost:5450/smt_onic"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
