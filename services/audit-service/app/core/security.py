import logging
from typing import Optional

from fastapi import HTTPException, Request, status
from jose import JWTError, jwt

from app.core.config import settings

logger = logging.getLogger(__name__)


def _decode_token(token: str) -> dict:
    """Decode a JWT token locally using RS256 (or HS256 fallback for dev).

    No HTTP call to auth-service. Public key is read from settings.
    """
    algorithm = settings.ALGORITHM

    # Use RS256 public key if configured; fall back to HS256 secret (dev only)
    if algorithm == "RS256" and settings.JWT_PUBLIC_KEY:
        key = settings.JWT_PUBLIC_KEY
    else:
        key = settings.JWT_PUBLIC_KEY
        algorithm = "HS256"

    try:
        payload = jwt.decode(token, key, algorithms=[algorithm])
        return payload
    except JWTError as exc:
        logger.warning(
            "JWT decode failed",
            extra={"service_task": "jwt_decode", "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(request: Request) -> dict:
    """Extract and validate the current user from the Authorization header.

    Returns the decoded JWT payload dict.
    Raises HTTP 401 if token is missing or invalid.
    """
    authorization: Optional[str] = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or malformed",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1]
    return _decode_token(token)


def require_roles(allowed_roles: list[str]):
    """Dependency factory: raise 403 if current user's role is not in allowed_roles."""

    def dependency(request: Request) -> dict:
        user = get_current_user(request)
        role = user.get("role", "")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' is not permitted to perform this action.",
            )
        return user

    return dependency
