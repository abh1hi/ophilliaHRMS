"""JWT-based internal service-to-service authentication (leave-service)."""
from datetime import datetime, timezone, timedelta
from fastapi import Header, HTTPException, status
from jose import jwt, JWTError

from app.core.config import settings

_ALGORITHM = "HS256"
_TOKEN_TTL_SECONDS = 300


def create_service_token(issuer: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"iss": issuer, "aud": "internal", "iat": now, "exp": now + timedelta(seconds=_TOKEN_TTL_SECONDS)},
        settings.INTERNAL_SERVICE_TOKEN, algorithm=_ALGORITHM,
    )


def verify_service_jwt(x_service_token: str = Header(...)) -> None:
    if x_service_token == settings.INTERNAL_SERVICE_TOKEN:
        return
    try:
        jwt.decode(x_service_token, settings.INTERNAL_SERVICE_TOKEN, algorithms=[_ALGORITHM], audience="internal")
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid internal token: {exc}")
