"""
Google integration endpoints.

GET  /google/auth/url           — build OAuth2 authorization URL
GET  /google/auth/callback      — exchange code, save tokens, redirect to frontend
GET  /google/status             — current integration status for the logged-in user
GET  /google/calendars          — list available Google calendars
POST /google/calendars/connect  — save which calendars to sync
POST /google/sync/calendar      — trigger manual calendar sync
POST /google/sync/tasks         — trigger manual task sync
DELETE /google/disconnect       — revoke tokens and delete integration
GET  /google/notes              — list Google Keep notes
"""
import logging
from typing import List, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from googleapiclient.discovery import build as _build_service

from app.api.v1.dependencies import DB, AnyUser
from app.core.config import settings
from app.core.responses import APIResponse
from app.models.google_integration import GoogleIntegration
from app.repositories import google_repository as repo
from app.schemas.google_integration import (
    GoogleIntegrationResponse,
    ConnectCalendarsRequest,
    SyncLogResponse,
)
from app.services import (
    google_oauth_service as oauth_svc,
    google_calendar_sync as cal_sync,
    google_tasks_sync as task_sync,
    google_notes_service as notes_svc,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ── OAuth2 flow ────────────────────────────────────────────────────────────────

@router.get("/auth/url")
async def get_auth_url(current_user: AnyUser) -> APIResponse[dict]:
    """Return the Google OAuth2 authorization URL."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth2 is not configured on this server.",
        )
    url = oauth_svc.build_auth_url(state=current_user.sub)
    return APIResponse(success=True, data={"auth_url": url})


@router.get("/auth/callback", include_in_schema=False)
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(default=""),
    *,
    db: DB,
    current_user: AnyUser,
):
    """
    Google redirects here after the user grants consent.
    Exchanges the authorization code for tokens and persists the integration.
    Redirects the browser to the frontend workspace settings page.
    """
    try:
        tokens = oauth_svc.exchange_code(code)
    except Exception as exc:
        logger.error(f"OAuth code exchange failed: {exc}")
        raise HTTPException(status_code=400, detail="OAuth code exchange failed.")

    google_email = oauth_svc.get_google_email(tokens["access_token"])

    await oauth_svc.save_integration(
        db=db,
        employee_id=UUID(current_user.sub),
        company_id=current_user.company_id,
        access_token=tokens["access_token"],
        refresh_token=tokens.get("refresh_token", ""),
        token_expiry=tokens.get("token_expiry"),
        scopes=tokens.get("scopes", ""),
        google_email=google_email,
    )
    await db.commit()

    # Redirect back to the frontend
    frontend_url = settings.ALLOWED_ORIGINS[0] if settings.ALLOWED_ORIGINS else "http://localhost:3000"
    return RedirectResponse(url=f"{frontend_url}?tab=workspace-settings&google=connected")


# ── Integration status ─────────────────────────────────────────────────────────

@router.get("/status", response_model=APIResponse[GoogleIntegrationResponse])
async def get_status(*, db: DB, current_user: AnyUser):
    """Return the current Google integration for the logged-in user."""
    integration = await repo.get_integration(db, UUID(current_user.sub), current_user.company_id)
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Google integration found.")
    return APIResponse(success=True, data=integration)


# ── Calendar management ────────────────────────────────────────────────────────

@router.get("/calendars", response_model=APIResponse[List[dict]])
async def list_google_calendars(*, db: DB, current_user: AnyUser):
    """List calendars available on the user's Google account."""
    integration = await _get_integration_or_404(db, current_user)
    try:
        creds = await oauth_svc.ensure_valid_credentials(db, integration)
        service = _build_service("calendar", "v3", credentials=creds, cache_discovery=False)
        resp = service.calendarList().list().execute()
        items = resp.get("items", [])
        calendars = [
            {
                "id": c.get("id"),
                "summary": c.get("summary"),
                "description": c.get("description"),
                "primary": c.get("primary", False),
                "accessRole": c.get("accessRole"),
                "backgroundColor": c.get("backgroundColor"),
            }
            for c in items
        ]
    except Exception as exc:
        logger.error(f"Failed to list Google calendars: {exc}")
        raise HTTPException(status_code=502, detail="Failed to fetch Google calendars.")
    return APIResponse(success=True, data=calendars)


@router.post("/calendars/connect", response_model=APIResponse[GoogleIntegrationResponse])
async def connect_calendars(data: ConnectCalendarsRequest, *, db: DB, current_user: AnyUser):
    """Save the selected Google calendar IDs to sync."""
    integration = await _get_integration_or_404(db, current_user)
    try:
        creds = await oauth_svc.ensure_valid_credentials(db, integration)
        service = _build_service("calendar", "v3", credentials=creds, cache_discovery=False)
        # Fetch metadata for each selected calendar
        connected = []
        for cal_id in data.calendar_ids:
            try:
                cal = service.calendars().get(calendarId=cal_id).execute()
                connected.append({
                    "id": cal.get("id"),
                    "summary": cal.get("summary"),
                    "primary": cal.get("id") == "primary",
                    "backgroundColor": cal.get("backgroundColor"),
                })
            except Exception:
                connected.append({"id": cal_id, "summary": cal_id, "primary": False})
        integration.connected_calendars = connected
        await db.flush()
        await db.commit()
    except Exception as exc:
        logger.error(f"Failed to connect calendars: {exc}")
        raise HTTPException(status_code=502, detail="Failed to connect calendars.")
    return APIResponse(success=True, data=integration)


# ── Manual sync triggers ───────────────────────────────────────────────────────

@router.post("/sync/calendar", response_model=APIResponse[dict])
async def trigger_calendar_sync(*, db: DB, current_user: AnyUser):
    """Manually trigger a Google Calendar sync for the current user."""
    integration = await _get_integration_or_404(db, current_user)
    result = await cal_sync.sync_calendar_for_integration(db, integration)
    await db.commit()
    return APIResponse(success=True, data=result)


@router.post("/sync/tasks", response_model=APIResponse[dict])
async def trigger_task_sync(*, db: DB, current_user: AnyUser):
    """Manually trigger a Google Tasks sync for the current user."""
    integration = await _get_integration_or_404(db, current_user)
    result = await task_sync.sync_tasks_for_integration(db, integration)
    await db.commit()
    return APIResponse(success=True, data=result)


# ── Disconnect ─────────────────────────────────────────────────────────────────

@router.delete("/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_google(*, db: DB, current_user: AnyUser):
    """Revoke the Google integration and clear stored tokens."""
    integration = await repo.get_integration(db, UUID(current_user.sub), current_user.company_id)
    if not integration:
        return

    # Best-effort token revocation
    try:
        if integration.access_token:
            access = oauth_svc.decrypt_token(integration.access_token)
            import urllib.request
            urllib.request.urlopen(
                f"https://oauth2.googleapis.com/revoke?token={access}",
                timeout=5,
            )
    except Exception:
        pass

    await repo.soft_delete_integration(db, integration)
    await db.commit()


# ── Google Keep notes ──────────────────────────────────────────────────────────

@router.get("/notes", response_model=APIResponse[List[Any]])
async def list_keep_notes(
    page_size: int = Query(default=50, ge=1, le=200),
    *,
    db: DB,
    current_user: AnyUser,
):
    """
    List Google Keep notes for the current user.
    Requires a Google Workspace (G Suite) account — returns 403 for personal Gmail.
    """
    integration = await _get_integration_or_404(db, current_user)
    try:
        notes = await notes_svc.list_keep_notes(db, integration, page_size=page_size)
    except notes_svc.WorkspaceAccountRequired as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error(f"Keep notes error: {exc}")
        raise HTTPException(status_code=502, detail="Failed to fetch Keep notes.")
    return APIResponse(success=True, data=notes)


# ── Helper ─────────────────────────────────────────────────────────────────────

async def _get_integration_or_404(db, current_user) -> GoogleIntegration:
    integration = await repo.get_integration(db, UUID(current_user.sub), current_user.company_id)
    if not integration or integration.status == "revoked":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google account not connected. Please connect via /google/auth/url.",
        )
    return integration
