from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.db.session import get_db
from app.models.notification import NotificationLog
from app.schemas.notification import NotificationLogResponse
from app.api.v1.dependencies import (
    get_current_user,
    require_role,
    TokenPayload,
    get_db_with_tenant
)
from app.core.constants import UserRole

router = APIRouter()

@router.get("/", response_model=List[NotificationLogResponse])
async def get_notification_logs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: TokenPayload = Depends(get_current_user)
):
    import uuid as _uuid
    # Scope by tenant
    raw_cid = db.info.get("company_id")
    company_id = _uuid.UUID(raw_cid) if isinstance(raw_cid, str) else raw_cid
    query = select(NotificationLog).filter(NotificationLog.company_id == company_id)

    if current_user.role == UserRole.EMPLOYEE.value:
        uid = _uuid.UUID(current_user.sub)
        query = query.filter(NotificationLog.user_id == uid)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
