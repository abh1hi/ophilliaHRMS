from uuid import UUID
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.calendar_event import CalendarEvent
from app.models.recurrence_override import RecurrenceOverride


async def get_event(db: AsyncSession, event_id: UUID, company_id: str) -> Optional[CalendarEvent]:
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.id == event_id,
            CalendarEvent.company_id == company_id,
            CalendarEvent.is_deleted == False,
        )
    )
    return result.scalars().first()


async def list_events_in_range(
    db: AsyncSession,
    company_id: str,
    start: datetime,
    end: datetime,
    calendar_id: Optional[UUID] = None,
    event_type: Optional[str] = None,
) -> List[CalendarEvent]:
    q = select(CalendarEvent).where(
        CalendarEvent.company_id == company_id,
        CalendarEvent.is_deleted == False,
        CalendarEvent.start_time <= end,
        CalendarEvent.end_time >= start,
    )
    if calendar_id:
        q = q.where(CalendarEvent.calendar_id == calendar_id)
    if event_type:
        q = q.where(CalendarEvent.event_type == event_type)
    result = await db.execute(q.order_by(CalendarEvent.start_time))
    return result.scalars().all()


async def get_recurrence_overrides(db: AsyncSession, master_event_id: UUID) -> List[RecurrenceOverride]:
    result = await db.execute(
        select(RecurrenceOverride).where(RecurrenceOverride.master_event_id == master_event_id)
    )
    return result.scalars().all()


async def get_override(db: AsyncSession, master_event_id: UUID, override_date) -> Optional[RecurrenceOverride]:
    result = await db.execute(
        select(RecurrenceOverride).where(
            RecurrenceOverride.master_event_id == master_event_id,
            RecurrenceOverride.override_date == override_date,
        )
    )
    return result.scalars().first()
