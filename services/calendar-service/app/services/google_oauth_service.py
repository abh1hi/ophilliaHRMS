"""
Google OAuth2 service — handles token exchange, refresh, and Fernet encryption at rest.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.google_integration import GoogleIntegration
from app.repositories import google_repository as repo

logger = logging.getLogger(__name__)

# Google API scopes needed
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks",
    # Keep API requires Google Workspace — included but may 403 on personal accounts
    "https://www.googleapis.com/auth/keep",
]


def _build_flow() -> Flow:
    return Flow.from_client_config(
        client_config={
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )


def build_auth_url(state: Optional[str] = None) -> str:
    """Build the Google OAuth2 authorization URL."""
    flow = _build_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",  # Force consent to always get refresh_token
        state=state or "",
    )
    return auth_url


async def exchange_code(code: str) -> dict:
    """Exchange authorization code for access + refresh tokens."""
    flow = _build_flow()
    flow.fetch_token(code=code)
    creds = flow.credentials
    return {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_expiry": creds.expiry,
        "scopes": " ".join(creds.scopes or SCOPES),
    }


def get_google_email(access_token: str) -> Optional[str]:
    """Fetch the user's Google email using the People/OAuth2 userinfo endpoint."""
    import urllib.request, json as _json
    req = urllib.request.Request(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            info = _json.loads(resp.read())
            return info.get("email")
    except Exception as exc:
        logger.warning(f"Could not fetch Google user info: {exc}")
        return None


# ── Fernet encryption helpers ──────────────────────────────────────────────────

def _fernet() -> Optional[Fernet]:
    if not settings.TOKEN_ENCRYPTION_KEY:
        return None
    try:
        return Fernet(settings.TOKEN_ENCRYPTION_KEY.encode())
    except Exception:
        return None


def encrypt_token(raw: str) -> str:
    f = _fernet()
    if not f:
        return raw
    return f.encrypt(raw.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    f = _fernet()
    if not f:
        return encrypted
    try:
        return f.decrypt(encrypted.encode()).decode()
    except InvalidToken:
        logger.warning("Failed to decrypt Google token — treating as plaintext")
        return encrypted


# ── Credentials object ─────────────────────────────────────────────────────────

def build_credentials(integration: GoogleIntegration) -> Credentials:
    """Build a google.oauth2.credentials.Credentials from a stored integration."""
    access_token = decrypt_token(integration.access_token) if integration.access_token else None
    refresh_token = decrypt_token(integration.refresh_token) if integration.refresh_token else None
    return Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=integration.scopes.split() if integration.scopes else SCOPES,
    )


async def ensure_valid_credentials(
    db: AsyncSession,
    integration: GoogleIntegration,
) -> Credentials:
    """
    Return valid credentials, refreshing the access token if it has expired.
    Persists the updated token back to the database.
    """
    creds = build_credentials(integration)

    is_expired = (
        integration.token_expiry is None
        or integration.token_expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc) + timedelta(minutes=5)
    )

    if is_expired and creds.refresh_token:
        try:
            creds.refresh(GoogleAuthRequest())
            # Persist refreshed tokens
            integration.access_token = encrypt_token(creds.token)
            if creds.expiry:
                integration.token_expiry = creds.expiry.replace(tzinfo=timezone.utc)
            await db.flush()
        except Exception as exc:
            logger.error(f"Token refresh failed for integration {integration.id}: {exc}")
            raise

    return creds


async def save_integration(
    db: AsyncSession,
    employee_id: UUID,
    company_id: str,
    access_token: str,
    refresh_token: str,
    token_expiry: Optional[datetime],
    scopes: str,
    google_email: Optional[str],
) -> GoogleIntegration:
    """Create or update a GoogleIntegration record."""
    existing = await repo.get_integration(db, employee_id, company_id)

    enc_access = encrypt_token(access_token)
    enc_refresh = encrypt_token(refresh_token) if refresh_token else None

    if existing:
        existing.access_token = enc_access
        if enc_refresh:
            existing.refresh_token = enc_refresh
        existing.token_expiry = token_expiry
        existing.scopes = scopes
        existing.status = "active"
        existing.sync_error_count = 0
        existing.next_sync_allowed_at = None
        if google_email:
            existing.google_email = google_email
        await db.flush()
        return existing

    from app.models.google_integration import GoogleIntegration as Model
    integration = Model(
        employee_id=employee_id,
        company_id=company_id,
        google_email=google_email,
        access_token=enc_access,
        refresh_token=enc_refresh,
        token_expiry=token_expiry,
        scopes=scopes,
        status="active",
        connected_calendars=[],
    )
    db.add(integration)
    await db.flush()
    return integration
