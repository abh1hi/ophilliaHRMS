"""Holidays CRUD endpoint — HR/Admin only."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.models.leave import Holiday
from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.utils.holiday_cache import invalidate_holiday_cache
from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional

router = APIRouter()


class HolidayCreate(BaseModel):
    name: str
    date: date
    description: Optional[str] = None


class HolidayResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    date: date
    description: Optional[str] = None
    is_active: int
    created_at: datetime
    updated_at: datetime


@router.post("/", response_model=HolidayResponse, status_code=status.HTTP_201_CREATED)
async def create_holiday(
    data: HolidayCreate,
    _user: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    obj = Holiday(**data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    invalidate_holiday_cache()
    return obj


@router.get("/", response_model=List[HolidayResponse])
async def list_holidays(
    _user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    result = await db.execute(select(Holiday).where(Holiday.is_active == 1).order_by(Holiday.date))
    return result.scalars().all()


@router.delete("/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holiday(
    holiday_id: UUID,
    _user: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    result = await db.execute(select(Holiday).where(Holiday.id == holiday_id))
    obj = result.scalars().first()
    if not obj:
        raise HTTPException(status_code=404, detail="Holiday not found")
    obj.is_active = 0
    db.add(obj)
    await db.commit()
    invalidate_holiday_cache()
