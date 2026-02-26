from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # ── Project ──────────────────────────────────────────
    PROJECT_NAME: str = "Students Service"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:changeme@localhost:5432/students_db"

    # ── Auth (JWT RS256 public key from auth-service) ────
    AUTH_SERVICE_URL: str = "http://auth-service:8000"
    JWT_PUBLIC_KEY: str = ""
    JWT_ALGORITHM: str = "RS256"

    # ── RabbitMQ ─────────────────────────────────────────
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/2"

    # ── CORS ─────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = ["http://localhost", "http://localhost:3000"]

    # ── Pagination ───────────────────────────────────────
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
