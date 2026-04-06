from fastapi import APIRouter, status, UploadFile, File
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date

from app.api.v1.dependencies import DB, AnyUser
from app.schemas.calendar_event import (
    EventCreate, EventUpdate, RSVPRequest, OccurrenceOverrideRequest,
    CalendarEventResponse,
)
from app.core.responses import APIResponse
from app.repositories import event_repository as repo
from app.services import event_service as svc
from app.utils.recurrence import expand_recurring_events

router = APIRouter()


@router.get("/", response_model=APIResponse[List[CalendarEventResponse]])
async def list_events(
    calendar_id: Optional[UUID] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    event_type: Optional[str] = None,
    *,
    db: DB,
    current_user: AnyUser,
):
    from datetime import timezone
    s = start or datetime(2000, 1, 1, tzinfo=timezone.utc)
    e = end or datetime(2100, 1, 1, tzinfo=timezone.utc)
    items = await repo.list_events_in_range(db, current_user.company_id, s, e, calendar_id, event_type)
    return APIResponse(success=True, data=items)


@router.get("/range", response_model=APIResponse[List[dict]])
async def get_events_range(
    start: datetime,
    end: datetime,
    calendar_id: Optional[UUID] = None,
    *,
    db: DB,
    current_user: AnyUser,
):
    """FullCalendar-style range query — expands RRULE instances with overrides."""
    from app.core.cache import cache_get, cache_set, events_range_key
    cache_key = events_range_key(current_user.company_id, str(start.date()), str(end.date()))
    cached = await cache_get(cache_key)
    if cached:
        return APIResponse(success=True, data=cached)

    events = await repo.list_events_in_range(db, current_user.company_id, start, end, calendar_id)
    expanded = await expand_recurring_events(db, events, start, end)
    await cache_set(cache_key, expanded, ttl=60)
    return APIResponse(success=True, data=expanded)


@router.post("/", response_model=APIResponse[CalendarEventResponse], status_code=status.HTTP_201_CREATED)
async def create_event(data: EventCreate, *, db: DB, current_user: AnyUser):
    event = await svc.create_event(db, data, UUID(current_user.sub), current_user.company_id)
    return APIResponse(success=True, data=event)


@router.get("/{event_id}", response_model=APIResponse[CalendarEventResponse])
async def get_event(event_id: UUID, *, db: DB, current_user: AnyUser):
    event = await repo.get_event(db, event_id, current_user.company_id)
    if not event:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Event not found")
    return APIResponse(success=True, data=event)


@router.patch("/{event_id}", response_model=APIResponse[CalendarEventResponse])
async def update_event(event_id: UUID, data: EventUpdate, *, db: DB, current_user: AnyUser):
    event = await svc.update_event(db, event_id, data, UUID(current_user.sub), current_user.role, current_user.company_id)
    return APIResponse(success=True, data=event)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: UUID, *, db: DB, current_user: AnyUser):
    await svc.delete_event(db, event_id, UUID(current_user.sub), current_user.role, current_user.company_id)


@router.post("/{event_id}/rsvp", response_model=APIResponse[CalendarEventResponse])
async def rsvp(event_id: UUID, data: RSVPRequest, *, db: DB, current_user: AnyUser):
    event = await svc.rsvp_event(db, event_id, UUID(current_user.sub), data.rsvp_status, current_user.company_id)
    return APIResponse(success=True, data=event)


@router.patch("/{event_id}/occurrences/{override_date}", response_model=APIResponse[dict])
async def edit_occurrence(
    event_id: UUID,
    override_date: date,
    data: OccurrenceOverrideRequest,
    *,
    db: DB,
    current_user: AnyUser,
):
    override = await svc.override_occurrence(
        db, event_id, override_date, data,
        UUID(current_user.sub), current_user.role, current_user.company_id,
    )
    return APIResponse(success=True, data={"id": str(override.id), "action": override.action})


@router.delete("/{event_id}/occurrences/{override_date}", response_model=APIResponse[dict])
async def skip_occurrence(
    event_id: UUID,
    override_date: date,
    *,
    db: DB,
    current_user: AnyUser,
):
    override = await svc.skip_occurrence(
        db, event_id, override_date,
        UUID(current_user.sub), current_user.role, current_user.company_id,
    )
    return APIResponse(success=True, data={"id": str(override.id), "action": override.action})
