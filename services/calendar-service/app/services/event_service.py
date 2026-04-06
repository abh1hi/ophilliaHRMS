from datetime import datetime, timezone, date
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar_event import CalendarEvent
from app.models.recurrence_override import RecurrenceOverride
from app.schemas.calendar_event import EventCreate, EventUpdate, OccurrenceOverrideRequest
from app.repositories import event_repository as repo
from app.repositories import calendar_repository as cal_repo
from app.core.permissions import check_permission
from app.core.cache import cache_invalidate, company_events_pattern


async def create_event(db: AsyncSession, data: EventCreate, created_by: UUID, company_id: str) -> CalendarEvent:
    cal = await cal_repo.get_calendar(db, data.calendar_id, company_id)
    if not cal:
        raise HTTPException(status_code=404, detail="Calendar not found")
    check_permission("event:create", "", created_by)  # any authenticated user

    event = CalendarEvent(
        **data.model_dump(exclude={"attendees"}),
        attendees=[a.model_dump() for a in data.attendees],
        created_by=created_by,
        company_id=company_id,
    )
    db.add(event)
    await db.commit()
    await cache_invalidate(company_events_pattern(company_id))
    return event


async def update_event(
    db: AsyncSession, event_id: UUID, data: EventUpdate,
    current_user_id: UUID, current_user_role: str, company_id: str
) -> CalendarEvent:
    event = await repo.get_event(db, event_id, company_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    check_permission("event:update", current_user_role, current_user_id, event.created_by)

    update_data = data.model_dump(exclude_unset=True)
    if "attendees" in update_data and update_data["attendees"] is not None:
        update_data["attendees"] = [a.model_dump() for a in update_data["attendees"]]
    for field, value in update_data.items():
        setattr(event, field, value)
    await db.commit()
    await cache_invalidate(company_events_pattern(company_id))
    return event


async def delete_event(
    db: AsyncSession, event_id: UUID,
    current_user_id: UUID, current_user_role: str, company_id: str
) -> None:
    event = await repo.get_event(db, event_id, company_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    check_permission("event:delete", current_user_role, current_user_id, event.created_by)
    event.is_deleted = True
    event.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    await cache_invalidate(company_events_pattern(company_id))


async def rsvp_event(db: AsyncSession, event_id: UUID, employee_id: UUID, rsvp_status: str, company_id: str) -> CalendarEvent:
    event = await repo.get_event(db, event_id, company_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    attendees = list(event.attendees or [])
    for att in attendees:
        if str(att.get("employee_id")) == str(employee_id):
            att["rsvp_status"] = rsvp_status
            break
    else:
        attendees.append({"employee_id": str(employee_id), "rsvp_status": rsvp_status})
    event.attendees = attendees
    await db.commit()
    return event


async def override_occurrence(
    db: AsyncSession, event_id: UUID, override_date: date, data: OccurrenceOverrideRequest,
    current_user_id: UUID, current_user_role: str, company_id: str
) -> RecurrenceOverride:
    event = await repo.get_event(db, event_id, company_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if not event.rrule:
        raise HTTPException(status_code=400, detail="Event is not a recurring event")
    check_permission("event:update", current_user_role, current_user_id, event.created_by)

    existing = await repo.get_override(db, event_id, override_date)
    if existing:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
        await db.commit()
        return existing

    override = RecurrenceOverride(
        master_event_id=event_id,
        override_date=override_date,
        action="edit",
        company_id=company_id,
        **data.model_dump(exclude_unset=True),
    )
    db.add(override)
    await db.commit()
    return override


async def skip_occurrence(
    db: AsyncSession, event_id: UUID, override_date: date,
    current_user_id: UUID, current_user_role: str, company_id: str
) -> RecurrenceOverride:
    event = await repo.get_event(db, event_id, company_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if not event.rrule:
        raise HTTPException(status_code=400, detail="Event is not a recurring event")
    check_permission("event:delete", current_user_role, current_user_id, event.created_by)

    existing = await repo.get_override(db, event_id, override_date)
    if existing:
        existing.action = "skip"
        await db.commit()
        return existing

    override = RecurrenceOverride(
        master_event_id=event_id,
        override_date=override_date,
        action="skip",
        company_id=company_id,
    )
    db.add(override)
    await db.commit()
    return override
