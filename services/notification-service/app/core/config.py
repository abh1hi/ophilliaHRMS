from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union
from pydantic import field_validator
import json


class Settings(BaseSettings):
    PROJECT_NAME: str = "HRMS Notification Service"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_DB: str = "notification_db"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:changeme@hrms-db:5432/notification_db"

    # Security — JWT validation
    JWT_PUBLIC_KEY: str = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAkHp7+dBXMZc8rNzUUdy+
5RJzhGEs2oMjZ1O3B2XzXcgLrm+3N6GTvB/jg8SMSicTmABn27hrwabpR+81yHJs
FSDwCyhDHLxFoofWMfzwmt2DWB6Ky5o9qC86U2fxzFNWlnhkzTDZpHI97LhHZw10
jvKcML8A0H0unUZKk9rwcbTuoRnk1O7KXaYvr1K4K4W8WTzjLdA0ljXOAu00Z5FY
jT80OSNdWOfTE81prfRXMf9FnI8y4BaQsl2rExC/Y1ipGxZfgTGsYZtvX18p2Mz2
Z8tXeQep4DBeYIuzue20ivYB35xBP5GplYLaol7S+UQwRVxGGJ+cDpfq76u+FyXz
OwIDAQAB
-----END PUBLIC KEY-----"""
    ALGORITHM: str = "RS256"

    # Service URLs
    AUTH_SERVICE_URL: str = "http://auth-service:8000"
    EMPLOYEE_SERVICE_URL: str = "http://employee-service:8001"
    INTERNAL_SERVICE_TOKEN: str = "CHANGE_THIS_INTERNAL_TOKEN_IN_PRODUCTION"

    # Redis (shared blacklist with auth-service)
    REDIS_URL: str = "redis://hrms-redis:6379/0"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    # SMTP — Real email delivery
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@ophillia.com"
    SMTP_FROM_NAME: str = "Ophillia HRMS"
    SMTP_USE_TLS: bool = True

    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:3000"]

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
