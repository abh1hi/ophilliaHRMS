from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union
from pydantic import field_validator
import json


class Settings(BaseSettings):
    PROJECT_NAME: str = "HRMS Auth Service"
    API_V1_STR: str = "/api/v1"

    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "auth_db"
    DATABASE_URL: str
    SUPERADMIN_DATABASE_URL: str = ""  # Restricted role for super admin — same host, limited table access

    # Security — keys are required, must be supplied via env (no hardcoded defaults)
    JWT_PRIVATE_KEY: str
    JWT_PUBLIC_KEY: str
    ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    MAGIC_LINK_EXPIRE_MINUTES: int = 15

    # Redis — for JWT blacklist (logout/revocation)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Debug — disables Swagger UI when False
    DEBUG: bool = False

    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:3000"]

    # Frontend URL for magic links / password reset emails
    FRONTEND_URL: str = "http://localhost:3000"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    # Internal service auth
    INTERNAL_SERVICE_TOKEN: str = "CHANGE_THIS_INTERNAL_TOKEN_IN_PRODUCTION"

    # Onboarding service (for post-login context enrichment)
    ONBOARDING_SERVICE_URL: str = "http://onboarding-service:8006"

    @field_validator("JWT_PRIVATE_KEY", "JWT_PUBLIC_KEY", mode="before")
    @classmethod
    def unescape_pem(cls, v: str) -> str:
        """Allow PEM keys stored as single-line strings with literal \\n."""
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
