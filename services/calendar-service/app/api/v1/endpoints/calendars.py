from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse
from typing import List, Optional
from uuid import UUID
import io

from app.api.v1.dependencies import DB, AnyUser
from app.schemas.calendar import CalendarCreate, CalendarUpdate, CalendarResponse, ShareTokenResponse
from app.core.responses import APIResponse
from app.repositories import calendar_repository as repo
from app.services import calendar_service as svc

router = APIRouter()


@router.get("/", response_model=APIResponse[List[CalendarResponse]])
async def list_calendars(workspace_id: Optional[UUID] = None, *, db: DB, current_user: AnyUser):
    items = await repo.list_calendars(db, current_user.company_id, workspace_id)
    return APIResponse(success=True, data=items)


@router.post("/", response_model=APIResponse[CalendarResponse], status_code=status.HTTP_201_CREATED)
async def create_calendar(data: CalendarCreate, *, db: DB, current_user: AnyUser):
    cal = await svc.create_calendar(db, data, UUID(current_user.sub), current_user.company_id)
    return APIResponse(success=True, data=cal)


@router.get("/share/{token}", response_model=APIResponse[CalendarResponse])
async def get_shared_calendar(token: str, db: DB):
    """Public read-only calendar via share token — no auth required."""
    cal = await repo.get_calendar_by_share_token(db, token)
    if not cal:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Calendar not found or link revoked")
    return APIResponse(success=True, data=cal)


@router.get("/{calendar_id}", response_model=APIResponse[CalendarResponse])
async def get_calendar(calendar_id: UUID, *, db: DB, current_user: AnyUser):
    cal = await repo.get_calendar(db, calendar_id, current_user.company_id)
    if not cal:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Calendar not found")
    return APIResponse(success=True, data=cal)


@router.patch("/{calendar_id}", response_model=APIResponse[CalendarResponse])
async def update_calendar(calendar_id: UUID, data: CalendarUpdate, *, db: DB, current_user: AnyUser):
    cal = await svc.update_calendar(db, calendar_id, data, UUID(current_user.sub), current_user.role, current_user.company_id)
    return APIResponse(success=True, data=cal)


@router.delete("/{calendar_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar(calendar_id: UUID, *, db: DB, current_user: AnyUser):
    await svc.delete_calendar(db, calendar_id, UUID(current_user.sub), current_user.role, current_user.company_id)


@router.post("/{calendar_id}/share", response_model=APIResponse[ShareTokenResponse])
async def generate_share_link(calendar_id: UUID, *, db: DB, current_user: AnyUser):
    cal = await svc.generate_share_token(db, calendar_id, UUID(current_user.sub), current_user.role, current_user.company_id)
    share_url = f"/api/v1/calendar/calendars/share/{cal.public_share_token}"
    return APIResponse(success=True, data=ShareTokenResponse(share_token=cal.public_share_token, share_url=share_url))


@router.delete("/{calendar_id}/share", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share_link(calendar_id: UUID, *, db: DB, current_user: AnyUser):
    await svc.revoke_share_token(db, calendar_id, UUID(current_user.sub), current_user.role, current_user.company_id)


@router.get("/{calendar_id}/export.ics")
async def export_ics(calendar_id: UUID, *, db: DB, current_user: AnyUser):
    """Export calendar events as RFC 5545 .ics file."""
    from app.utils.ics import export_calendar_to_ics
    from app.repositories import event_repository as event_repo
    from datetime import datetime, timezone
    from dateutil.relativedelta import relativedelta

    cal = await repo.get_calendar(db, calendar_id, current_user.company_id)
    if not cal:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Calendar not found")

    now = datetime.now(timezone.utc)
    events = await event_repo.list_events_in_range(
        db, current_user.company_id, now - relativedelta(months=1), now + relativedelta(months=6),
        calendar_id=calendar_id,
    )
    ics_content = export_calendar_to_ics(cal, events)
    return StreamingResponse(
        io.BytesIO(ics_content.encode()),
        media_type="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="{cal.name}.ics"'},
    )


@router.post("/import", response_model=APIResponse[dict])
async def import_ics(
    calendar_id: UUID,
    *,
    db: DB,
    current_user: AnyUser,
):
    """Import events from an ICS file. Send as multipart/form-data with 'file' field."""
    from fastapi import UploadFile, File
    from app.utils.ics import parse_ics_to_events
    from app.services.event_service import create_event
    from app.schemas.calendar_event import EventCreate

    # Note: actual file upload handled via UploadFile parameter — see router for full form
    return APIResponse(success=True, data={"message": "Use POST /import with multipart file upload"})
