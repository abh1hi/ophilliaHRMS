"""JWT-based internal service-to-service authentication.

Tokens are short-lived (5-minute TTL), signed with HMAC-SHA256.
Each service identifies itself via the `iss` claim.

Usage — client (caller):
    token = create_service_token("onboarding-service")
    headers = {"X-Service-Token": token}

Usage — server (FastAPI dependency):
    @router.post("/...", dependencies=[Depends(verify_service_jwt)])
"""
from datetime import datetime, timezone, timedelta
from fastapi import Header, HTTPException, status
from jose import jwt, JWTError

from app.core.config import settings

_ALGORITHM = "HS256"
_TOKEN_TTL_SECONDS = 300  # 5 minutes


def create_service_token(issuer: str, audience: str = "onboarding-service") -> str:
    """Create a short-lived JWT signed with INTERNAL_SERVICE_TOKEN."""
    now = datetime.now(timezone.utc)
    payload = {
        "iss": issuer,
        "aud": audience,
        "service": issuer,
        "iat": now,
        "exp": now + timedelta(seconds=_TOKEN_TTL_SECONDS),
    }
    return jwt.encode(payload, settings.INTERNAL_SERVICE_TOKEN, algorithm=_ALGORITHM)


def verify_service_jwt(x_service_token: str = Header(...)) -> None:
    """Validate internal service JWT. audience must be 'onboarding-service' or legacy 'internal'."""
    try:
        payload = jwt.decode(
            x_service_token,
            settings.INTERNAL_SERVICE_TOKEN,
            algorithms=[_ALGORITHM],
            options={"verify_aud": False},
        )
        aud = payload.get("aud", "")
        if aud not in ("onboarding-service", "internal"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token audience invalid for onboarding-service",
            )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired internal service token: {exc}",
        )
