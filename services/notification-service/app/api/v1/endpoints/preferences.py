from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.api.v1.dependencies import (
    get_current_user,
    TokenPayload,
    get_db_with_tenant
)
from app.services import notification_service
from app.schemas.notification import PreferenceResponse, PreferenceUpdate

router = APIRouter()

@router.get("/", response_model=PreferenceResponse)
async def get_my_preferences(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: TokenPayload = Depends(get_current_user)
):
    import uuid
    uid = uuid.UUID(current_user.sub)
    return await notification_service.get_or_create_preference(db, uid)

@router.put("/", response_model=PreferenceResponse)
async def update_my_preferences(
    *,
    db: AsyncSession = Depends(get_db_with_tenant),
    pref_in: PreferenceUpdate,
    current_user: TokenPayload = Depends(get_current_user)
):
    import uuid
    uid = uuid.UUID(current_user.sub)
    return await notification_service.update_preference(db, uid, pref_in)
