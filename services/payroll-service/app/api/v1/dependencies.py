from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.security import get_current_user, require_role, verify_service_token, TokenPayload
from app.services.payroll_service import PayrollService
from app.core.constants import UserRole


async def get_db_with_tenant(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AsyncSession:
    db.info["company_id"] = current_user.company_id
    return db


async def get_payroll_service(db: AsyncSession = Depends(get_db_with_tenant)) -> PayrollService:
    return PayrollService(db)


def require_hr_or_admin():
    return require_role(UserRole.HR, UserRole.SUPER_ADMIN)
