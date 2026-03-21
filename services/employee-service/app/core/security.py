from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from pydantic import BaseModel
import os

from app.core.config import settings
from app.core.constants import UserRole

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.AUTH_SERVICE_URL}/api/v1/auth/login"
)


class TokenPayload(BaseModel):
    """Decoded JWT payload."""
    sub: str        # user_id (UUID)
    role: str       # employee | manager | hr | super_admin
    email: str
    company_id: str


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    """Decode and validate JWT from Authorization header.

    Returns a TokenPayload with user_id, role, email, and company_id.
    Does NOT call auth-service — validates locally using shared SECRET_KEY.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_PUBLIC_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        email: str = payload.get("email")
        company_id: str = payload.get("company_id")

        if not user_id or not role or not company_id:
            raise credentials_exception

        jti = payload.get("jti")
        if jti:
            from app.core.token_blacklist import is_blacklisted
            if await is_blacklisted(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        return TokenPayload(
            sub=user_id,
            role=role,
            email=email or "",
            company_id=company_id
        )

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please refresh your token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception


def require_role(*allowed_roles: UserRole):
    """Dependency factory to enforce RBAC roles.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            user: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.HR))
        ):
            ...
    """
    def role_checker(
        current_user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        if UserRole(current_user.role) not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {[r.value for r in allowed_roles]}",
            )
        return current_user
    return role_checker


def verify_service_token(x_service_token: str = Header(...)) -> None:
    """Validate the internal service-to-service token.

    Use as a dependency on internal-only endpoints:
        @router.get("/internal/...", dependencies=[Depends(verify_service_token)])
    """
    if x_service_token != settings.INTERNAL_SERVICE_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid internal service token",
        )
