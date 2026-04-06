"""Leave Period service — CRUD for LeavePeriod with tenant scoping."""
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.leave_period import LeavePeriod
from app.schemas.leave_period import LeavePeriodCreate, LeavePeriodUpdate


def _company_id(db: AsyncSession) -> UUID:
    cid = db.info.get("company_id")
    if not cid:
        raise RuntimeError("company_id not set on session")
    return UUID(cid) if isinstance(cid, str) else cid


async def list_periods(
    db: AsyncSession,
    include_inactive: bool = False,
    skip: int = 0,
    limit: int = 50,
) -> tuple[List[LeavePeriod], int]:
    cid = _company_id(db)
    q = select(LeavePeriod).where(LeavePeriod.company_id == cid)
    if not include_inactive:
        q = q.where(LeavePeriod.is_active == 1)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar() or 0
    items = (await db.execute(q.order_by(LeavePeriod.from_date.desc()).offset(skip).limit(limit))).scalars().all()
    return list(items), total


async def create_period(db: AsyncSession, data: LeavePeriodCreate) -> LeavePeriod:
    cid = _company_id(db)
    obj = LeavePeriod(**data.model_dump(), company_id=cid)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def get_period(db: AsyncSession, period_id: UUID) -> LeavePeriod:
    cid = _company_id(db)
    obj = (await db.execute(
        select(LeavePeriod).where(LeavePeriod.id == period_id, LeavePeriod.company_id == cid)
    )).scalars().first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave period not found")
    return obj


async def update_period(db: AsyncSession, period_id: UUID, data: LeavePeriodUpdate) -> LeavePeriod:
    obj = await get_period(db, period_id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


async def delete_period(db: AsyncSession, period_id: UUID) -> LeavePeriod:
    obj = await get_period(db, period_id)
    obj.is_active = 0
    await db.commit()
    await db.refresh(obj)
    return obj
