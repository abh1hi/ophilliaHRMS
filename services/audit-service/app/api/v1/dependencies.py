from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.security import get_current_user, require_roles
from app.db.session import get_db
from app.services.audit_service import AuditService


def require_hr_or_admin(request: Request) -> dict:
    """Allow HR, Manager, Super Admin roles."""
    return require_roles(["hr", "manager", "super_admin", "admin"])(request)


def require_super_admin(request: Request) -> dict:
    """Allow Super Admin only."""
    return require_roles(["super_admin"])(request)


async def apply_tenant_context(db: AsyncSession, company_id: str) -> None:
    """Set company_id in both session info dict and PostgreSQL session variable for RLS."""
    db.info["company_id"] = company_id
    await db.execute(text("SELECT set_config('app.company_id', :cid, true)"), {"cid": company_id})


async def get_db_with_tenant(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AsyncSession:
    user = get_current_user(request)
    jwt_company_id = user.get("company_id", "")

    gateway_company_id = request.headers.get("X-Company-ID")
    if gateway_company_id and gateway_company_id != jwt_company_id:
        raise HTTPException(status_code=403, detail="Tenant context mismatch")

    if jwt_company_id:
        await apply_tenant_context(db, jwt_company_id)
    return db


async def get_audit_service(db: AsyncSession = Depends(get_db_with_tenant)) -> AuditService:
    """Dependency that injects an AuditService with a scoped DB session."""
    return AuditService(db)
