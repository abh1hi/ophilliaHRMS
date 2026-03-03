from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_roles
from app.db.session import get_db
from app.services.audit_service import AuditService


def require_hr_or_admin(request: Request) -> dict:
    """Allow HR, Manager, Super Admin roles."""
    return require_roles(["hr", "manager", "super_admin"])(request)


def require_super_admin(request: Request) -> dict:
    """Allow Super Admin only."""
    return require_roles(["super_admin"])(request)


async def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    """Dependency that injects an AuditService with a scoped DB session."""
    return AuditService(db)
