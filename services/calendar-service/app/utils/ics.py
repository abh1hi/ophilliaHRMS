"""ICS import/export using the icalendar library (RFC 5545)."""
from datetime import datetime, timezone
from typing import List
from uuid import uuid4

try:
    from icalendar import Calendar as ICalendar, Event as ICalEvent
    HAS_ICALENDAR = True
except ImportError:
    HAS_ICALENDAR = False


def export_calendar_to_ics(calendar, events: list) -> str:
    """Export a calendar and its events to RFC 5545 ICS string."""
    if not HAS_ICALENDAR:
        raise RuntimeError("icalendar package not installed")

    cal = ICalendar()
    cal.add("prodid", "-//Ophillia HRMS//Calendar//EN")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", calendar.name)
    if calendar.description:
        cal.add("x-wr-caldesc", calendar.description)

    for event in events:
        vevent = ICalEvent()
        vevent.add("uid", str(event.id))
        vevent.add("summary", event.title)
        if event.description:
            vevent.add("description", event.description)
        if event.location:
            vevent.add("location", event.location)
        vevent.add("dtstart", event.start_time)
        vevent.add("dtend", event.end_time)
        vevent.add("dtstamp", datetime.now(timezone.utc))
        if event.rrule:
            vevent.add("rrule", _parse_rrule_for_ical(event.rrule))
        cal.add_component(vevent)

    return cal.to_ical().decode("utf-8")


def parse_ics_to_events(ics_content: bytes, calendar_id: str, company_id: str) -> list:
    """Parse an ICS file and return a list of EventCreate-like dicts."""
    if not HAS_ICALENDAR:
        raise RuntimeError("icalendar package not installed")

    cal = ICalendar.from_ical(ics_content)
    events = []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue
        dtstart = component.get("dtstart")
        dtend = component.get("dtend")
        if not dtstart or not dtend:
            continue

        start_dt = dtstart.dt
        end_dt = dtend.dt

        # Convert date to datetime if all_day
        all_day = not hasattr(start_dt, "hour")
        if all_day:
            from datetime import datetime as dt
            start_dt = dt.combine(start_dt, dt.min.time()).replace(tzinfo=timezone.utc)
            end_dt = dt.combine(end_dt, dt.min.time()).replace(tzinfo=timezone.utc)
        elif start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
            end_dt = end_dt.replace(tzinfo=timezone.utc)

        rrule_str = None
        if "rrule" in component:
            rrule_str = component["rrule"].to_ical().decode()

        events.append({
            "calendar_id": calendar_id,
            "title": str(component.get("summary", "Imported Event")),
            "description": str(component.get("description", "")) or None,
            "location": str(component.get("location", "")) or None,
            "start_time": start_dt,
            "end_time": end_dt,
            "all_day": all_day,
            "rrule": rrule_str,
            "event_type": "meeting",
            "timezone": "UTC",
        })

    return events


def _parse_rrule_for_ical(rrule_str: str) -> dict:
    """Convert an RRULE string to a dict for icalendar library."""
    if rrule_str.startswith("RRULE:"):
        rrule_str = rrule_str[6:]
    parts = {}
    for part in rrule_str.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            parts[k] = v
    return parts
