from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union
from pydantic import field_validator
import json


class Settings(BaseSettings):
    PROJECT_NAME: str = "HRMS Employee Service"
    API_V1_STR: str = "/api/v1"

    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_DB: str = "employee_db"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:changeme@employee-db:5432/employee_db"

    # Security — JWT validation (shared with auth-service); key must be supplied via env
    JWT_PUBLIC_KEY: str
    ALGORITHM: str = "RS256"

    # PII encryption — 64 hex chars = 32 bytes AES-256 key; must be supplied via env
    PII_ENCRYPTION_KEY: str

    # Debug — disables Swagger UI when False
    DEBUG: bool = False

    # Auth Service (service-to-service)
    AUTH_SERVICE_URL: str = "http://auth-service:8000"
    INTERNAL_SERVICE_TOKEN: str = "CHANGE_THIS_INTERNAL_TOKEN_IN_PRODUCTION"

    # Employee self-service app (used to construct invite URLs for HR to share)
    EMPLOYEE_APP_URL: str = "http://localhost:5174"

    # Redis (shared blacklist with auth-service)
    REDIS_URL: str = "redis://hrms-redis:6379/0"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:3000"]

    @field_validator("JWT_PUBLIC_KEY", mode="before")
    @classmethod
    def unescape_pem(cls, v: str) -> str:
        """Allow PEM key stored as single-line string with literal \\n."""
        return v.replace("\\n", "\n") if isinstance(v, str) else v

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
