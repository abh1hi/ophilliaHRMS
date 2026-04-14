"""Leave Block List service — manage dates on which leave applications are blocked."""
from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.leave_block_list import LeaveBlockList, LeaveBlockListDate, LeaveBlockListAllowed
from app.schemas.leave_block_list import (
    LeaveBlockListCreate, LeaveBlockListUpdate,
    LeaveBlockListDateCreate, LeaveBlockListAllowedCreate,
)


def _cid(db: AsyncSession) -> UUID:
    cid = db.info.get("company_id")
    return UUID(cid) if isinstance(cid, str) else cid


async def list_block_lists(db: AsyncSession, include_inactive: bool = False) -> List[LeaveBlockList]:
    cid = _cid(db)
    q = select(LeaveBlockList).where(LeaveBlockList.company_id == cid)
    if not include_inactive:
        q = q.where(LeaveBlockList.is_active == 1)
    return list((await db.execute(q)).scalars().all())


async def get_block_list(db: AsyncSession, block_list_id: UUID) -> LeaveBlockList:
    cid = _cid(db)
    obj = (await db.execute(
        select(LeaveBlockList).where(
            LeaveBlockList.id == block_list_id, LeaveBlockList.company_id == cid
        )
    )).scalars().first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Block list not found")
    return obj


async def create_block_list(db: AsyncSession, data: LeaveBlockListCreate) -> LeaveBlockList:
    cid = _cid(db)
    obj = LeaveBlockList(
        name=data.name,
        applies_to_company=data.applies_to_company,
        company_id=cid,
    )
    for d in data.dates:
        obj.dates.append(LeaveBlockListDate(**d.model_dump(), company_id=cid))
    for u in data.allowed_users:
        obj.allowed_users.append(LeaveBlockListAllowed(**u.model_dump(), company_id=cid))
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def update_block_list(
    db: AsyncSession, block_list_id: UUID, data: LeaveBlockListUpdate
) -> LeaveBlockList:
    obj = await get_block_list(db, block_list_id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


async def is_date_blocked(db: AsyncSession, target_date: date) -> bool:
    """Check if a given date is in any active company-wide block list."""
    cid = _cid(db)
    row = (await db.execute(
        select(LeaveBlockListDate)
        .join(LeaveBlockList, LeaveBlockListDate.block_list_id == LeaveBlockList.id)
        .where(
            and_(
                LeaveBlockList.company_id == cid,
                LeaveBlockList.is_active == 1,
                LeaveBlockList.applies_to_company == 1,
                LeaveBlockListDate.block_date == target_date,
            )
        )
        .limit(1)
    )).scalars().first()
    return row is not None
