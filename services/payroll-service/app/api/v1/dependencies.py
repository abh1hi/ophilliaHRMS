from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db
from app.core.security import get_current_user, require_role, verify_service_token, TokenPayload
from app.services.payroll_service import PayrollService
from app.core.constants import UserRole


async def apply_tenant_context(db: AsyncSession, company_id: str) -> None:
    """Set company_id in both session info dict and PostgreSQL session variable for RLS."""
    db.info["company_id"] = company_id
    await db.execute(text("SELECT set_config('app.company_id', :cid, true)"), {"cid": company_id})


async def get_db_with_tenant(
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AsyncSession:
    jwt_company_id = current_user.company_id

    gateway_company_id = request.headers.get("X-Company-ID")
    if gateway_company_id and gateway_company_id != jwt_company_id:
        raise HTTPException(status_code=403, detail="Tenant context mismatch")

    await apply_tenant_context(db, jwt_company_id)
    return db


async def get_payroll_service(db: AsyncSession = Depends(get_db_with_tenant)) -> PayrollService:
    return PayrollService(db)


def require_hr_or_admin():
    return require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
