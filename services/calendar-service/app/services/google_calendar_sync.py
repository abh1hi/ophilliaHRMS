"""
Google Calendar ↔ HRMS two-way sync.

Strategy:
  • Inbound  (Google → HRMS): incremental sync using nextSyncToken per integration.
    New/updated Google events are upserted into calendar_events (matched on google_event_id).
    Deleted Google events (status='cancelled') soft-delete the local record.

  • Outbound (HRMS → Google): when an event has google_event_id=None but belongs to a
    Google-synced calendar, we push it to Google and record the returned ID.

Exponential backoff: on repeated errors sync_error_count increments and
next_sync_allowed_at is set to min(60 * 2^n, 3600) seconds in the future.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID

from googleapiclient.discovery import build as _build_service
from googleapiclient.errors import HttpError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.calendar_event import CalendarEvent
from app.models.calendar import Calendar
from app.models.google_integration import GoogleIntegration
from app.models.sync_log import SyncLog
from app.services.google_oauth_service import ensure_valid_credentials
from app.repositories.google_repository import (
    get_last_sync_token,
    save_sync_log,
    mark_integration_error,
    mark_integration_success,
)

logger = logging.getLogger(__name__)


def _parse_dt(dt_dict: Optional[dict]) -> Optional[datetime]:
    """Parse a Google Calendar dateTime or date dict into an aware datetime."""
    if not dt_dict:
        return None
    if "dateTime" in dt_dict:
        raw = dt_dict["dateTime"]
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    if "date" in dt_dict:
        raw = dt_dict["date"]
        try:
            return datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _is_all_day(event: dict) -> bool:
    return "date" in event.get("start", {})


def _rrule_from_google(recurrence: list) -> Optional[str]:
    """Extract the first RRULE line from Google's recurrence list."""
    for line in recurrence or []:
        if line.startswith("RRULE:"):
            return line
    return None


async def _get_or_create_sync_calendar(
    db: AsyncSession,
    integration: GoogleIntegration,
    company_id: str,
) -> Optional[Calendar]:
    """
    Return the first google_synced calendar owned by this employee, or None.
    The frontend connects specific Google calendars via POST /google/calendars/connect.
    """
    result = await db.execute(
        select(Calendar).where(
            Calendar.company_id == company_id,
            Calendar.owner_id == integration.employee_id,
            Calendar.calendar_type == "google_synced",
            Calendar.is_deleted == False,
        ).limit(1)
    )
    return result.scalars().first()


async def sync_calendar_for_integration(
    db: AsyncSession,
    integration: GoogleIntegration,
) -> dict:
    """
    Run a full inbound sync for one GoogleIntegration.
    Returns {"synced": N, "failed": N} summary.
    """
    company_id = str(integration.company_id)
    now = datetime.now(timezone.utc)

    # Respect backoff window
    if integration.next_sync_allowed_at and integration.next_sync_allowed_at > now:
        logger.info(f"Skipping sync for {integration.id} — backoff until {integration.next_sync_allowed_at}")
        return {"synced": 0, "failed": 0}

    try:
        creds = await ensure_valid_credentials(db, integration)
    except Exception as exc:
        logger.error(f"Credential refresh failed for {integration.id}: {exc}")
        await mark_integration_error(db, integration)
        return {"synced": 0, "failed": 1}

    service = _build_service("calendar", "v3", credentials=creds, cache_discovery=False)

    synced = 0
    failed = 0

    # Sync each connected calendar
    for cal_meta in (integration.connected_calendars or []):
        google_cal_id = cal_meta.get("id")
        if not google_cal_id:
            continue

        # Look up (or find) our local calendar for this Google calendar ID
        local_cal_result = await db.execute(
            select(Calendar).where(
                Calendar.company_id == company_id,
                Calendar.google_calendar_id == google_cal_id,
                Calendar.is_deleted == False,
            ).limit(1)
        )
        local_cal = local_cal_result.scalars().first()

        if not local_cal:
            # Create a mirror calendar
            local_cal = Calendar(
                company_id=company_id,
                owner_id=integration.employee_id,
                name=cal_meta.get("summary", "Google Calendar"),
                calendar_type="google_synced",
                google_calendar_id=google_cal_id,
                color=cal_meta.get("backgroundColor"),
                is_default=cal_meta.get("primary", False),
            )
            db.add(local_cal)
            await db.flush()

        # Get last sync token for incremental sync
        sync_token = await get_last_sync_token(db, integration.id, google_cal_id)
        new_sync_token: Optional[str] = None

        try:
            if sync_token:
                request = service.events().list(
                    calendarId=google_cal_id,
                    syncToken=sync_token,
                )
            else:
                # Full sync — last 90 days + 365 days ahead
                time_min = (now - timedelta(days=90)).isoformat()
                time_max = (now + timedelta(days=365)).isoformat()
                request = service.events().list(
                    calendarId=google_cal_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=False,
                    maxResults=2500,
                )

            while request is not None:
                response = request.execute()
                items = response.get("items", [])
                new_sync_token = response.get("nextSyncToken")

                for g_event in items:
                    try:
                        await _upsert_event(db, g_event, local_cal, integration.employee_id, company_id)
                        synced += 1
                    except Exception as e:
                        logger.warning(f"Failed to upsert event {g_event.get('id')}: {e}")
                        failed += 1

                page_token = response.get("nextPageToken")
                if page_token:
                    request = service.events().list(
                        calendarId=google_cal_id,
                        pageToken=page_token,
                    )
                else:
                    request = None

        except HttpError as exc:
            if exc.resp.status == 410:
                # Sync token expired — do a full re-sync next time
                logger.warning(f"Sync token expired for cal {google_cal_id}, resetting")
                await _reset_sync_token(db, integration.id, google_cal_id)
            else:
                logger.error(f"Google Calendar API error for {google_cal_id}: {exc}")
                failed += 1
            continue

        # Save new sync token
        if new_sync_token:
            await save_sync_log(
                db,
                employee_id=integration.employee_id,
                integration_id=integration.id,
                resource_type="calendar_event",
                local_resource_id=None,
                google_resource_id=google_cal_id,
                sync_direction="inbound",
                sync_status="success",
                next_sync_token=new_sync_token,
            )

    # Outbound: push local events that haven't been synced to Google yet
    out_synced, out_failed = await _push_new_local_events(db, integration, service, company_id)
    synced += out_synced
    failed += out_failed

    await mark_integration_success(db, integration)
    logger.info(f"Sync done for {integration.id}: {synced} synced, {failed} failed")
    return {"synced": synced, "failed": failed}


async def _upsert_event(
    db: AsyncSession,
    g_event: dict,
    local_cal: Calendar,
    employee_id: UUID,
    company_id: str,
) -> None:
    """Create or update a local CalendarEvent from a Google Calendar event dict."""
    google_event_id = g_event.get("id")
    if not google_event_id:
        return

    # Check if the event is cancelled (deleted on Google side)
    if g_event.get("status") == "cancelled":
        await _soft_delete_event(db, google_event_id, company_id)
        return

    start = _parse_dt(g_event.get("start"))
    end = _parse_dt(g_event.get("end"))
    if not start or not end:
        return

    all_day = _is_all_day(g_event)
    rrule = _rrule_from_google(g_event.get("recurrence"))

    # Try to find existing
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.google_event_id == google_event_id,
            CalendarEvent.is_deleted == False,
        ).limit(1)
    )
    existing = result.scalars().first()

    if existing:
        existing.title = g_event.get("summary", existing.title)
        existing.description = g_event.get("description")
        existing.location = g_event.get("location")
        existing.start_time = start
        existing.end_time = end
        existing.all_day = all_day
        existing.rrule = rrule
        existing.google_etag = g_event.get("etag")
        existing.status = "cancelled" if g_event.get("status") == "cancelled" else "scheduled"
    else:
        new_event = CalendarEvent(
            calendar_id=local_cal.id,
            company_id=company_id,
            title=g_event.get("summary", "(No title)"),
            description=g_event.get("description"),
            location=g_event.get("location"),
            event_type="meeting",
            start_time=start,
            end_time=end,
            all_day=all_day,
            timezone=g_event.get("start", {}).get("timeZone", "UTC"),
            rrule=rrule,
            status="scheduled",
            created_by=employee_id,
            attendees=[],
            google_event_id=google_event_id,
            google_etag=g_event.get("etag"),
            reminder_minutes=[],
        )
        db.add(new_event)

    await db.flush()


async def _soft_delete_event(db: AsyncSession, google_event_id: str, company_id: str) -> None:
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.google_event_id == google_event_id,
            CalendarEvent.is_deleted == False,
        )
    )
    ev = result.scalars().first()
    if ev:
        ev.is_deleted = True
        ev.deleted_at = datetime.now(timezone.utc)
        await db.flush()


async def _push_new_local_events(
    db: AsyncSession,
    integration: GoogleIntegration,
    service,
    company_id: str,
) -> tuple[int, int]:
    """
    Push local events that belong to a google_synced calendar
    but haven't been pushed to Google yet (google_event_id is None).
    """
    synced = failed = 0
    result = await db.execute(
        select(CalendarEvent)
        .join(Calendar, CalendarEvent.calendar_id == Calendar.id)
        .where(
            Calendar.company_id == company_id,
            Calendar.owner_id == integration.employee_id,
            Calendar.calendar_type == "google_synced",
            CalendarEvent.google_event_id == None,  # noqa: E711
            CalendarEvent.is_deleted == False,
        )
        .limit(100)
    )
    local_events = result.scalars().all()

    for ev in local_events:
        # Find which google calendar to push to
        local_cal_result = await db.execute(
            select(Calendar).where(Calendar.id == ev.calendar_id)
        )
        local_cal = local_cal_result.scalars().first()
        if not local_cal or not local_cal.google_calendar_id:
            continue

        body = _event_to_google_body(ev)
        try:
            created = service.events().insert(
                calendarId=local_cal.google_calendar_id,
                body=body,
            ).execute()
            ev.google_event_id = created.get("id")
            ev.google_etag = created.get("etag")
            await db.flush()
            synced += 1
        except HttpError as exc:
            logger.warning(f"Failed to push event {ev.id} to Google: {exc}")
            failed += 1

    return synced, failed


def _event_to_google_body(ev: CalendarEvent) -> dict:
    """Convert a local CalendarEvent to Google Calendar API request body."""
    def _dt_str(dt: datetime) -> str:
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    body: dict = {
        "summary": ev.title,
        "description": ev.description or "",
        "location": ev.location or "",
        "start": {"date": ev.start_time.date().isoformat()} if ev.all_day
                 else {"dateTime": _dt_str(ev.start_time), "timeZone": ev.timezone or "UTC"},
        "end":   {"date": ev.end_time.date().isoformat()} if ev.all_day
                 else {"dateTime": _dt_str(ev.end_time),   "timeZone": ev.timezone or "UTC"},
    }
    if ev.rrule:
        body["recurrence"] = [ev.rrule]
    return body


async def _reset_sync_token(
    db: AsyncSession,
    integration_id: UUID,
    google_cal_id: str,
) -> None:
    """Clear sync tokens for a calendar so the next run does a full sync."""
    result = await db.execute(
        select(SyncLog).where(
            SyncLog.integration_id == integration_id,
            SyncLog.google_resource_id == google_cal_id,
            SyncLog.next_sync_token != None,
        )
    )
    for log in result.scalars().all():
        log.next_sync_token = None
    await db.flush()
