"""Holiday calendar CRUD — manage public holidays used by the overtime engine."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.core.responses import ok
from app.models.holiday_calendar import Holiday, HolidayCalendar
from app.schemas.overtime import (
    HolidayCalendarCreate, HolidayCalendarUpdate, HolidayCalendarResponse,
    HolidayCreate, HolidayResponse,
)

router = APIRouter(prefix="/holiday-calendars", tags=["holiday-calendars"])

_HR_ROLES = require_role(UserRole.HR, UserRole.ADMIN, UserRole.SUPER_ADMIN)


def _company_id(db: AsyncSession) -> UUID:
    cid = db.info.get("company_id")
    if not cid:
        raise RuntimeError("company_id not set on session")
    return UUID(cid) if isinstance(cid, str) else cid


async def _get_calendar(calendar_id: UUID, db: AsyncSession) -> HolidayCalendar:
    result = await db.execute(
        select(HolidayCalendar).where(
            HolidayCalendar.company_id == _company_id(db),
            HolidayCalendar.id == calendar_id,
        )
    )
    cal = result.scalars().first()
    if not cal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday calendar not found")
    return cal


@router.get("")
async def list_holiday_calendars(
    year: int | None = Query(None),
    _: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    stmt = select(HolidayCalendar).where(HolidayCalendar.company_id == _company_id(db))
    if year:
        stmt = stmt.where(HolidayCalendar.year == year)
    stmt = stmt.order_by(HolidayCalendar.year.desc(), HolidayCalendar.name)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return ok([HolidayCalendarResponse.model_validate(c).model_dump(mode="json") for c in items])


@router.post("", status_code=201)
async def create_holiday_calendar(
    data: HolidayCalendarCreate,
    _: TokenPayload = Depends(_HR_ROLES),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    cal = HolidayCalendar(company_id=_company_id(db), **data.model_dump())
    db.add(cal)
    await db.flush()
    await db.refresh(cal)
    await db.commit()
    return ok(HolidayCalendarResponse.model_validate(cal).model_dump(mode="json"))


@router.patch("/{calendar_id}")
async def update_holiday_calendar(
    calendar_id: UUID,
    data: HolidayCalendarUpdate,
    _: TokenPayload = Depends(_HR_ROLES),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    cal = await _get_calendar(calendar_id, db)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(cal, field, value)
    await db.flush()
    await db.commit()
    return ok(HolidayCalendarResponse.model_validate(cal).model_dump(mode="json"))


@router.delete("/{calendar_id}")
async def delete_holiday_calendar(
    calendar_id: UUID,
    _: TokenPayload = Depends(_HR_ROLES),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    cal = await _get_calendar(calendar_id, db)
    cal.is_active = False
    await db.flush()
    await db.commit()
    return ok(HolidayCalendarResponse.model_validate(cal).model_dump(mode="json"))


@router.get("/{calendar_id}/holidays")
async def list_holidays(
    calendar_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    cal = await _get_calendar(calendar_id, db)
    result = await db.execute(
        select(Holiday).where(Holiday.calendar_id == cal.id).order_by(Holiday.date)
    )
    items = result.scalars().all()
    return ok([HolidayResponse.model_validate(h).model_dump(mode="json") for h in items])


@router.post("/{calendar_id}/holidays", status_code=201)
async def add_holiday(
    calendar_id: UUID,
    data: HolidayCreate,
    _: TokenPayload = Depends(_HR_ROLES),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    cal = await _get_calendar(calendar_id, db)
    holiday = Holiday(calendar_id=cal.id, **data.model_dump())
    db.add(holiday)
    await db.flush()
    await db.refresh(holiday)
    await db.commit()
    return ok(HolidayResponse.model_validate(holiday).model_dump(mode="json"))


@router.delete("/{calendar_id}/holidays/{holiday_id}", status_code=204)
async def remove_holiday(
    calendar_id: UUID,
    holiday_id: UUID,
    _: TokenPayload = Depends(_HR_ROLES),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    cal = await _get_calendar(calendar_id, db)
    result = await db.execute(
        select(Holiday).where(Holiday.calendar_id == cal.id, Holiday.id == holiday_id)
    )
    holiday = result.scalars().first()
    if not holiday:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")
    await db.delete(holiday)
    await db.commit()
