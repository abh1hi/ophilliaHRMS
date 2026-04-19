from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from jose import jwt, JWTError

from app.core.config import settings
from app.db.session import get_db, get_db_superadmin
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.core.constants import UserRole
from app.core.token_blacklist import is_blacklisted

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_PUBLIC_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        jti: str | None = payload.get("jti")
        if jti and await is_blacklisted(jti):
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    return user


def require_role(*roles: UserRole):
    """Dependency factory to enforce RBAC roles."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if UserRole(current_user.role) not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {[r.value for r in roles]}",
            )
        return current_user
    return role_checker


async def apply_tenant_context(db: AsyncSession, company_id: str) -> None:
    """Set company_id in both session info dict and PostgreSQL session variable for RLS."""
    db.info["company_id"] = company_id
    await db.execute(text("SET LOCAL app.company_id = :cid"), {"cid": company_id})


async def get_db_with_tenant(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AsyncSession:
    """DB session with tenant context set — for all non-super-admin routes."""
    jwt_company_id = str(current_user.company_id)

    # Cross-check: gateway-injected header must match JWT claim (3-layer isolation)
    gateway_company_id = request.headers.get("X-Company-ID")
    if gateway_company_id and gateway_company_id != jwt_company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context mismatch")

    await apply_tenant_context(db, jwt_company_id)
    return db


async def get_super_admin_db(
    _sa: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db_superadmin),
) -> AsyncSession:
    """DB session using restricted super admin PostgreSQL role — companies + users tables only."""
    return db


def verify_internal_token(request: Request) -> None:
    """Validate the internal service-to-service X-Service-Token header.

    Accepts either a signed JWT (preferred) or the raw secret string (legacy fallback).
    For JWT tokens: validates signature, 'audience' claim must be 'auth-service',
    and 'service' claim must identify the calling service.
    """
    token = request.headers.get("X-Service-Token", "")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing internal service token",
        )

    # Try JWT validation first (audience + service identity check)
    try:
        payload = jwt.decode(
            token,
            settings.INTERNAL_SERVICE_TOKEN,
            algorithms=["HS256"],
            audience="auth-service",
        )
        service_name = payload.get("service")
        if not service_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Internal token missing service identity claim",
            )
        return  # JWT valid
    except JWTError:
        pass

    # Legacy fallback: raw shared secret comparison
    if token != settings.INTERNAL_SERVICE_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid internal service token",
        )
