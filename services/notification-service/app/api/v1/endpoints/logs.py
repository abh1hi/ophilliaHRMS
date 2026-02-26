from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.db.session import get_db
from app.models.notification import NotificationLog
from app.schemas.notification import NotificationLogResponse
from app.api.v1.dependencies import get_current_user, require_role, TokenPayload
from app.core.constants import UserRole

router = APIRouter()

@router.get("/", response_model=List[NotificationLogResponse])
async def get_notification_logs(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    query = select(NotificationLog)
    
    if current_user.role == UserRole.EMPLOYEE.value:
        import uuid
        uid = uuid.UUID(current_user.sub)
        query = query.filter(NotificationLog.user_id == uid)
        
    result = await db.execute(query)
    return result.scalars().all()
