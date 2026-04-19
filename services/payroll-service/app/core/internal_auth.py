"""JWT-based internal service-to-service authentication (payroll-service)."""
from datetime import datetime, timezone, timedelta
from fastapi import Header, HTTPException, status
from jose import jwt, JWTError

from app.core.config import settings

_ALGORITHM = "HS256"
_TOKEN_TTL_SECONDS = 300


def create_service_token(issuer: str, audience: str = "payroll-service") -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"iss": issuer, "aud": audience, "service": issuer, "iat": now, "exp": now + timedelta(seconds=_TOKEN_TTL_SECONDS)},
        settings.INTERNAL_SERVICE_TOKEN, algorithm=_ALGORITHM,
    )


def verify_service_jwt(x_service_token: str = Header(...)) -> None:
    """Validate internal service JWT. audience must be 'payroll-service' or legacy 'internal'."""
    try:
        payload = jwt.decode(
            x_service_token,
            settings.INTERNAL_SERVICE_TOKEN,
            algorithms=[_ALGORITHM],
            options={"verify_aud": False},
        )
        aud = payload.get("aud", "")
        if aud not in ("payroll-service", "internal"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token audience invalid for payroll-service")
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid internal token: {exc}")
