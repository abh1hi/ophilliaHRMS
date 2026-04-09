from typing import Annotated
from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role, TokenPayload
from app.core.constants import UserRole
from app.db.session import AsyncSessionLocal


async def get_db_with_tenant(current_user: TokenPayload = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        session.info["company_id"] = current_user.company_id
        yield session


# ── Annotated DI aliases ──────────────────────────────────────────────────────
DB = Annotated[AsyncSession, Depends(get_db_with_tenant)]
AnyUser = Annotated[TokenPayload, Depends(get_current_user)]
AdminUser = Annotated[TokenPayload, Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN))]
HRAdminUser = Annotated[TokenPayload, Depends(require_role(UserRole.HR, UserRole.ADMIN, UserRole.SUPER_ADMIN))]
