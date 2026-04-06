"""Holiday List service — manage named holiday lists and their assignments."""
from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holiday_list import HolidayList, HolidayListEntry
from app.models.holiday_list_assignment import HolidayListAssignment
from app.schemas.holiday_list import (
    HolidayListCreate, HolidayListUpdate,
    HolidayListAssignmentCreate, HolidayListEntryCreate,
)


def _cid(db: AsyncSession) -> UUID:
    cid = db.info.get("company_id")
    return UUID(cid) if isinstance(cid, str) else cid


# ── Holiday List CRUD ──────────────────────────────────────────────────────────

async def list_holiday_lists(
    db: AsyncSession, include_inactive: bool = False
) -> List[HolidayList]:
    cid = _cid(db)
    q = select(HolidayList).where(HolidayList.company_id == cid)
    if not include_inactive:
        q = q.where(HolidayList.is_active == 1)
    return list((await db.execute(q.order_by(HolidayList.from_date.desc()))).scalars().all())


async def get_holiday_list(db: AsyncSession, list_id: UUID) -> HolidayList:
    cid = _cid(db)
    obj = (await db.execute(
        select(HolidayList).where(HolidayList.id == list_id, HolidayList.company_id == cid)
    )).scalars().first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday list not found")
    return obj


async def create_holiday_list(db: AsyncSession, data: HolidayListCreate) -> HolidayList:
    cid = _cid(db)
    payload = data.model_dump(exclude={"entries"})
    obj = HolidayList(**payload, company_id=cid)
    for entry in data.entries:
        obj.entries.append(HolidayListEntry(**entry.model_dump()))
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def update_holiday_list(db: AsyncSession, list_id: UUID, data: HolidayListUpdate) -> HolidayList:
    obj = await get_holiday_list(db, list_id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


async def add_entries(
    db: AsyncSession, list_id: UUID, entries: List[HolidayListEntryCreate]
) -> HolidayList:
    obj = await get_holiday_list(db, list_id)
    for entry in entries:
        obj.entries.append(HolidayListEntry(holiday_list_id=obj.id, **entry.model_dump()))
    await db.commit()
    await db.refresh(obj)
    return obj


async def delete_holiday_list(db: AsyncSession, list_id: UUID) -> HolidayList:
    obj = await get_holiday_list(db, list_id)
    obj.is_active = 0
    await db.commit()
    await db.refresh(obj)
    return obj


# ── Holiday List Assignment ────────────────────────────────────────────────────

async def create_assignment(
    db: AsyncSession, data: HolidayListAssignmentCreate
) -> HolidayListAssignment:
    cid = _cid(db)
    obj = HolidayListAssignment(**data.model_dump(), company_id=cid)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_assignments(
    db: AsyncSession,
    employee_id: Optional[UUID] = None,
    applicable_for: Optional[str] = None,
) -> List[HolidayListAssignment]:
    cid = _cid(db)
    q = select(HolidayListAssignment).where(HolidayListAssignment.company_id == cid)
    if employee_id:
        q = q.where(HolidayListAssignment.employee_id == employee_id)
    if applicable_for:
        q = q.where(HolidayListAssignment.applicable_for == applicable_for)
    return list((await db.execute(q.order_by(HolidayListAssignment.assignment_from.desc()))).scalars().all())


async def get_active_holiday_list_for_employee(
    db: AsyncSession, employee_id: UUID, ref_date: date
) -> Optional[HolidayList]:
    """Return the most recent holiday list assigned to employee (or company fallback)."""
    cid = _cid(db)

    # Employee-level assignment first
    emp_row = (await db.execute(
        select(HolidayListAssignment)
        .where(
            and_(
                HolidayListAssignment.company_id == cid,
                HolidayListAssignment.employee_id == employee_id,
                HolidayListAssignment.applicable_for == "employee",
                HolidayListAssignment.assignment_from <= ref_date,
            )
        )
        .order_by(HolidayListAssignment.assignment_from.desc())
        .limit(1)
    )).scalars().first()

    if not emp_row:
        # Fall back to company-level
        emp_row = (await db.execute(
            select(HolidayListAssignment)
            .where(
                and_(
                    HolidayListAssignment.company_id == cid,
                    HolidayListAssignment.applicable_for == "company",
                    HolidayListAssignment.assignment_from <= ref_date,
                )
            )
            .order_by(HolidayListAssignment.assignment_from.desc())
            .limit(1)
        )).scalars().first()

    if not emp_row:
        return None

    return await get_holiday_list(db, emp_row.holiday_list_id)
