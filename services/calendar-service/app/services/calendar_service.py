import secrets
from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar import Calendar
from app.schemas.calendar import CalendarCreate, CalendarUpdate
from app.repositories import calendar_repository as repo
from app.core.permissions import check_permission


async def create_calendar(db: AsyncSession, data: CalendarCreate, owner_id: UUID, company_id: str) -> Calendar:
    cal = Calendar(**data.model_dump(), owner_id=owner_id, company_id=company_id)
    db.add(cal)
    await db.commit()
    await db.refresh(cal)
    return cal


async def update_calendar(
    db: AsyncSession, calendar_id: UUID, data: CalendarUpdate,
    current_user_id: UUID, current_user_role: str, company_id: str
) -> Calendar:
    cal = await repo.get_calendar(db, calendar_id, company_id)
    if not cal:
        raise HTTPException(status_code=404, detail="Calendar not found")
    check_permission("calendar:write", current_user_role, current_user_id, cal.owner_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cal, field, value)
    await db.commit()
    return cal


async def delete_calendar(
    db: AsyncSession, calendar_id: UUID,
    current_user_id: UUID, current_user_role: str, company_id: str
) -> None:
    cal = await repo.get_calendar(db, calendar_id, company_id)
    if not cal:
        raise HTTPException(status_code=404, detail="Calendar not found")
    check_permission("calendar:delete", current_user_role, current_user_id, cal.owner_id)
    cal.is_deleted = True
    cal.deleted_at = datetime.now(timezone.utc)
    await db.commit()


async def generate_share_token(
    db: AsyncSession, calendar_id: UUID,
    current_user_id: UUID, current_user_role: str, company_id: str
) -> Calendar:
    cal = await repo.get_calendar(db, calendar_id, company_id)
    if not cal:
        raise HTTPException(status_code=404, detail="Calendar not found")
    check_permission("calendar:write", current_user_role, current_user_id, cal.owner_id)
    cal.public_share_token = secrets.token_urlsafe(48)
    await db.commit()
    return cal


async def revoke_share_token(
    db: AsyncSession, calendar_id: UUID,
    current_user_id: UUID, current_user_role: str, company_id: str
) -> None:
    cal = await repo.get_calendar(db, calendar_id, company_id)
    if not cal:
        raise HTTPException(status_code=404, detail="Calendar not found")
    check_permission("calendar:write", current_user_role, current_user_id, cal.owner_id)
    cal.public_share_token = None
    await db.commit()
