from typing import Annotated
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.security import get_current_user, require_role, TokenPayload
from app.core.constants import UserRole
from app.db.session import AsyncSessionLocal


async def apply_tenant_context(db: AsyncSession, company_id: str) -> None:
    """Set company_id in both session info dict and PostgreSQL session variable for RLS."""
    db.info["company_id"] = company_id
    await db.execute(text("SET LOCAL app.company_id = :cid"), {"cid": company_id})


async def get_db_with_tenant(
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
):
    jwt_company_id = current_user.company_id

    gateway_company_id = request.headers.get("X-Company-ID")
    if gateway_company_id and gateway_company_id != jwt_company_id:
        raise HTTPException(status_code=403, detail="Tenant context mismatch")

    async with AsyncSessionLocal() as session:
        await apply_tenant_context(session, jwt_company_id)
        yield session


# ── Annotated DI aliases ──────────────────────────────────────────────────────
DB = Annotated[AsyncSession, Depends(get_db_with_tenant)]
AnyUser = Annotated[TokenPayload, Depends(get_current_user)]
AdminUser = Annotated[TokenPayload, Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN))]
HRAdminUser = Annotated[TokenPayload, Depends(require_role(UserRole.HR, UserRole.ADMIN, UserRole.SUPER_ADMIN))]
