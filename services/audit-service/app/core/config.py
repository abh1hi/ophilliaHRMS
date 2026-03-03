from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union
from pydantic import field_validator
import json


class Settings(BaseSettings):
    PROJECT_NAME: str = "HRMS Audit Service"
    API_V1_STR: str = "/api/v1"

    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_DB: str = "audit_db"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:changeme@hrms-db:5432/audit_db"

    # Security — RS256 local JWT validation (no round-trip to auth-service)
    SECRET_KEY: str = "CHANGE_THIS_TO_A_RANDOM_64_CHAR_SECRET_IN_PRODUCTION"
    ALGORITHM: str = "RS256"
    # RSA public key for RS256. When empty, falls back to HS256 SECRET_KEY (dev only).
    JWT_PUBLIC_KEY: str = ""

    # Internal service-to-service token
    INTERNAL_SERVICE_TOKEN: str = "CHANGE_THIS_INTERNAL_TOKEN_IN_PRODUCTION"

    # Auth Service URL (used for service-level health reference only — NOT for JWT validation)
    AUTH_SERVICE_URL: str = "http://auth-service:8000"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    # Audit log retention (days). Default 2 years.
    LOG_RETENTION_DAYS: int = 730

    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:3000"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [o.strip() for o in v.split(",")]
        return v

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")


settings = Settings()
