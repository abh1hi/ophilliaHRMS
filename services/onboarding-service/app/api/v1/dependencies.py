from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.core.config import settings
from app.core.constants import UserRole
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class TokenUser:
    """Lightweight user object extracted from JWT (no DB lookup needed)."""
    def __init__(self, user_id: str, company_id: str, role: str, email: str):
        self.id = user_id
        self.company_id = company_id
        self.role = role
        self.email = email


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_PUBLIC_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        company_id: str = payload.get("company_id")
        role: str = payload.get("role")
        email: str = payload.get("email", "")
        if user_id is None or company_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return TokenUser(user_id=user_id, company_id=company_id, role=role, email=email)


def require_role(*roles: UserRole):
    async def role_checker(current_user: TokenUser = Depends(get_current_user)) -> TokenUser:
        if UserRole(current_user.role) not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {[r.value for r in roles]}",
            )
        return current_user
    return role_checker
