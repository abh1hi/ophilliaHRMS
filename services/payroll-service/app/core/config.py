from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union
from pydantic import field_validator
import json


class Settings(BaseSettings):
    PROJECT_NAME: str = "HRMS Payroll Service"
    API_V1_STR: str = "/api/v1"

    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_DB: str = "payroll_db"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:changeme@hrms-db:5432/payroll_db"

    # Security — RS256 local JWT validation
    SECRET_KEY: str = "CHANGE_THIS_TO_A_RANDOM_64_CHAR_SECRET_IN_PRODUCTION"
    ALGORITHM: str = "RS256"
    JWT_PUBLIC_KEY: str = ""
    INTERNAL_SERVICE_TOKEN: str = "CHANGE_THIS_INTERNAL_TOKEN_IN_PRODUCTION"

    # Auth Service (health reference only)
    AUTH_SERVICE_URL: str = "http://auth-service:8000"

    # Employee Service (for employee verification)
    EMPLOYEE_SERVICE_URL: str = "http://employee-service:8001"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

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
