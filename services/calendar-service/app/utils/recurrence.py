"""RRULE expansion helpers with DST-safe recurrence_overrides support.

Uses python-dateutil for RFC 5545 RRULE parsing.
Never stores expanded occurrences in DB — expand on demand for /events/range.
"""
from datetime import datetime, timedelta, timezone, date
from typing import List, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.event_repository import get_recurrence_overrides


async def expand_recurring_events(
    db: AsyncSession,
    events: list,
    start: datetime,
    end: datetime,
) -> List[dict]:
    """Expand master events with RRULE into individual occurrences within [start, end].

    For each master event:
    1. Parse RRULE with dateutil.rrule
    2. Fetch recurrence_overrides for that event
    3. Substitute or skip overridden dates
    4. Return flat list of event dicts ready for FullCalendar
    """
    from dateutil.rrule import rrulestr
    from dateutil.parser import parse as dtparse

    result = []

    for event in events:
        event_dict = _event_to_dict(event)

        if not event.rrule:
            # Non-recurring — include as-is if in range
            if event.start_time <= end and event.end_time >= start:
                result.append(event_dict)
            continue

        # Fetch overrides for this master event
        overrides = await get_recurrence_overrides(db, event.id)
        override_map = {o.override_date: o for o in overrides}

        try:
            rule = rrulestr(event.rrule, dtstart=event.start_time, ignoretz=False)
        except Exception:
            # Malformed RRULE — include master event as-is
            result.append(event_dict)
            continue

        duration = event.end_time - event.start_time
        for occurrence_dt in rule.between(start - duration, end, inc=True):
            occ_date = occurrence_dt.date()

            if occ_date in override_map:
                override = override_map[occ_date]
                if override.action == "skip":
                    continue  # this occurrence is skipped
                # action == "edit" — use override values
                occ = dict(event_dict)
                occ["id"] = f"{event.id}_{occ_date.isoformat()}"
                occ["recurrence_master_id"] = str(event.id)
                occ["start_time"] = (override.new_start_time or occurrence_dt).isoformat()
                occ["end_time"] = (override.new_end_time or occurrence_dt + duration).isoformat()
                if override.new_title:
                    occ["title"] = override.new_title
                if override.new_description:
                    occ["description"] = override.new_description
                if override.new_location:
                    occ["location"] = override.new_location
                if override.new_all_day is not None:
                    occ["all_day"] = override.new_all_day
                result.append(occ)
            else:
                occ = dict(event_dict)
                occ["id"] = f"{event.id}_{occ_date.isoformat()}"
                occ["recurrence_master_id"] = str(event.id)
                occ["start_time"] = occurrence_dt.isoformat()
                occ["end_time"] = (occurrence_dt + duration).isoformat()
                result.append(occ)

    return result


def _event_to_dict(event) -> dict:
    return {
        "id": str(event.id),
        "calendar_id": str(event.calendar_id),
        "company_id": str(event.company_id),
        "title": event.title,
        "description": event.description,
        "location": event.location,
        "event_type": event.event_type,
        "start_time": event.start_time.isoformat() if event.start_time else None,
        "end_time": event.end_time.isoformat() if event.end_time else None,
        "all_day": event.all_day,
        "timezone": event.timezone,
        "rrule": event.rrule,
        "status": event.status,
        "created_by": str(event.created_by),
        "attendees": event.attendees or [],
        "color": event.color,
        "reminder_minutes": event.reminder_minutes or [],
    }
