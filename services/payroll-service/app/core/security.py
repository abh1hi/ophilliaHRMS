import logging
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings
from app.core.constants import UserRole

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.AUTH_SERVICE_URL}/api/v1/auth/login"
)


class TokenPayload(BaseModel):
    sub: str
    role: str
    email: str = ""
    company_id: str = ""


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    """Decode JWT locally using RS256 public key (or HS256 fallback for dev)."""
    algorithm = settings.ALGORITHM
    if algorithm == "RS256" and settings.JWT_PUBLIC_KEY:
        key = settings.JWT_PUBLIC_KEY
    else:
        key = settings.JWT_PUBLIC_KEY
        algorithm = "HS256"

    try:
        payload = jwt.decode(token, key, algorithms=[algorithm])
        user_id = payload.get("sub")
        role = payload.get("role")
        company_id = payload.get("company_id")
        if not user_id or not role or not company_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return TokenPayload(
            sub=user_id, role=role,
            email=payload.get("email", ""),
            company_id=company_id,
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(*allowed_roles: UserRole):
    def role_checker(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if UserRole(current_user.role) not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {[r.value for r in allowed_roles]}",
            )
        return current_user
    return role_checker


def verify_service_token(x_service_token: str = Header(...)) -> None:
    """Validate internal service-to-service token (X-Internal-Token header)."""
    if x_service_token != settings.INTERNAL_SERVICE_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid internal service token")
