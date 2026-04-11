from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union
from pydantic import field_validator
import json


class Settings(BaseSettings):
    PROJECT_NAME: str = "HRMS Onboarding Service"
    API_V1_STR: str = "/api/v1"

    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "onboarding_db"
    DATABASE_URL: str

    # Security — JWT verification (public key only, no signing)
    JWT_PUBLIC_KEY: str
    ALGORITHM: str = "RS256"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Debug
    DEBUG: bool = False

    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:3000"]

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    # Auth service for token validation
    AUTH_SERVICE_URL: str = "http://auth-service:8000"

    # Internal service auth
    INTERNAL_SERVICE_TOKEN: str = "CHANGE_THIS_INTERNAL_TOKEN_IN_PRODUCTION"

    # Domain service URLs (for template application saga)
    LEAVE_SERVICE_URL: str = "http://leave-service:8005"
    PAYROLL_SERVICE_URL: str = "http://payroll-service:8004"

    # Feature flags — default False; flip to True once verified in staging
    ENABLE_EVENT_DRIVEN_ONBOARDING: bool = False
    ENABLE_TEMPLATE_APPLICATION: bool = False

    @field_validator("JWT_PUBLIC_KEY", mode="before")
    @classmethod
    def unescape_pem(cls, v: str) -> str:
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
