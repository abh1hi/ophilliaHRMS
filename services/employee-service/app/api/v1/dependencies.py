from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.security import get_current_user, require_role, verify_service_token, TokenPayload

async def get_db_with_tenant(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AsyncSession:
    """Dependency that provides a DB session with company_id preset in info."""
    db.info["company_id"] = current_user.company_id
    return db

__all__ = ["get_current_user", "require_role", "verify_service_token", "TokenPayload", "get_db_with_tenant"]
