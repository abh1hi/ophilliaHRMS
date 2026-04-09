"""
Google Keep notes integration.

IMPORTANT: Google Keep API (v1) is only available for Google Workspace accounts.
Personal Gmail accounts will receive a 403 PERMISSION_DENIED error.

We attempt the API call and surface the limitation clearly in the response.
Docs: https://developers.google.com/keep/api/reference/rest
"""
import logging
from typing import Optional

from googleapiclient.discovery import build as _build_service
from googleapiclient.errors import HttpError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.google_integration import GoogleIntegration
from app.services.google_oauth_service import ensure_valid_credentials

logger = logging.getLogger(__name__)


class WorkspaceAccountRequired(Exception):
    """Raised when the Google Keep API returns 403 — user has a personal Gmail."""
    pass


async def list_keep_notes(
    db: AsyncSession,
    integration: GoogleIntegration,
    page_size: int = 50,
) -> list[dict]:
    """
    Fetch notes from Google Keep API.

    Raises:
        WorkspaceAccountRequired: if the account is a personal Gmail (403).
        Exception: for other API errors.
    """
    try:
        creds = await ensure_valid_credentials(db, integration)
    except Exception as exc:
        logger.error(f"Failed to get credentials for Keep notes: {exc}")
        raise

    try:
        service = _build_service("keep", "v1", credentials=creds, cache_discovery=False)
        response = service.notes().list(pageSize=page_size).execute()
        raw_notes = response.get("notes", [])
    except HttpError as exc:
        if exc.resp.status == 403:
            raise WorkspaceAccountRequired(
                "Google Keep API requires a Google Workspace (G Suite) account. "
                "Personal Gmail accounts cannot access Keep notes via API."
            )
        logger.error(f"Google Keep API error: {exc}")
        raise
    except Exception as exc:
        logger.error(f"Failed to fetch Keep notes: {exc}")
        raise

    return [_format_note(n) for n in raw_notes]


def _format_note(note: dict) -> dict:
    """Normalize a Google Keep API note to our internal schema."""
    body_parts = []
    body = note.get("body", {})

    if "text" in body:
        body_parts.append(body["text"].get("text", ""))
    elif "list" in body:
        for item in body["list"].get("listItems", []):
            checked = item.get("checked", False)
            text = item.get("text", {}).get("text", "")
            prefix = "✓ " if checked else "☐ "
            body_parts.append(prefix + text)

    title = note.get("title", "")
    body_text = "\n".join(body_parts)

    # Color mapping — Keep uses names like "YELLOW", "BLUE_GRAY", etc.
    color_map = {
        "DEFAULT": "#fef9c3",
        "RED": "#fecaca",
        "ORANGE": "#fed7aa",
        "YELLOW": "#fef9c3",
        "TEAL": "#ccfbf1",
        "BLUE": "#bfdbfe",
        "CERULEAN": "#e0f2fe",
        "GRAY": "#f1f5f9",
        "BLUE_GRAY": "#e2e8f0",
        "BLACK": "#f8fafc",
        "WHITE": "#ffffff",
        "BROWN": "#fef3c7",
        "UNSPECIFIED_COLOR": "#fef9c3",
    }
    color_name = note.get("color", "DEFAULT")
    color_hex = color_map.get(color_name, "#fef9c3")

    return {
        "id": note.get("name", ""),  # "notes/{id}"
        "title": title or None,
        "body": body_text,
        "color": color_hex,
        "is_pinned": note.get("isPinned", False),
        "is_trashed": note.get("trashed", False),
        "updated_at": note.get("updateTime", ""),
        "created_at": note.get("createTime", ""),
        "attachments": [
            {"mime_type": a.get("mimeType", ""), "name": a.get("name", "")}
            for a in note.get("attachments", [])
        ],
    }


async def get_keep_note(
    db: AsyncSession,
    integration: GoogleIntegration,
    note_name: str,
) -> Optional[dict]:
    """Fetch a single Keep note by its resource name (e.g. 'notes/abc123')."""
    try:
        creds = await ensure_valid_credentials(db, integration)
        service = _build_service("keep", "v1", credentials=creds, cache_discovery=False)
        note = service.notes().get(name=note_name).execute()
        return _format_note(note)
    except HttpError as exc:
        if exc.resp.status == 403:
            raise WorkspaceAccountRequired("Google Workspace account required.")
        if exc.resp.status == 404:
            return None
        raise
