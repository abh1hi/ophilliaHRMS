import logging
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.google_integration import GoogleIntegration
from app.models.sync_log import SyncLog

logger = logging.getLogger(__name__)


async def get_integration(db: AsyncSession, employee_id: UUID, company_id: str) -> Optional[GoogleIntegration]:
    result = await db.execute(
        select(GoogleIntegration).where(
            GoogleIntegration.employee_id == employee_id,
            GoogleIntegration.company_id == company_id,
            GoogleIntegration.is_deleted == False,
        )
    )
    return result.scalars().first()


async def list_active_integrations(db: AsyncSession) -> List[GoogleIntegration]:
    result = await db.execute(
        select(GoogleIntegration).where(
            GoogleIntegration.status == "active",
            GoogleIntegration.is_deleted == False,
        )
    )
    return result.scalars().all()


async def get_last_sync_token(
    db: AsyncSession,
    integration_id: UUID,
    google_cal_id: Optional[str] = None,
) -> Optional[str]:
    stmt = (
        select(SyncLog.next_sync_token)
        .where(
            SyncLog.integration_id == integration_id,
            SyncLog.next_sync_token != None,
        )
    )
    if google_cal_id:
        stmt = stmt.where(SyncLog.google_resource_id == google_cal_id)
    stmt = stmt.order_by(SyncLog.synced_at.desc()).limit(1)
    result = await db.execute(stmt)
    row = result.first()
    return row[0] if row else None


async def save_sync_log(
    db: AsyncSession,
    employee_id: UUID,
    integration_id: UUID,
    resource_type: str,
    local_resource_id: Optional[UUID],
    google_resource_id: Optional[str],
    sync_direction: str,
    sync_status: str,
    next_sync_token: Optional[str] = None,
    error_message: Optional[str] = None,
) -> SyncLog:
    log = SyncLog(
        employee_id=employee_id,
        integration_id=integration_id,
        resource_type=resource_type,
        local_resource_id=local_resource_id,
        google_resource_id=google_resource_id,
        sync_direction=sync_direction,
        sync_status=sync_status,
        next_sync_token=next_sync_token,
        error_message=error_message,
    )
    db.add(log)
    await db.flush()
    return log


async def mark_integration_error(
    db: AsyncSession,
    integration: GoogleIntegration,
) -> None:
    """Increment error count and set backoff window (exponential, capped at 1 hour)."""
    integration.sync_error_count = (integration.sync_error_count or 0) + 1
    delay_seconds = min(60 * (2 ** integration.sync_error_count), 3600)
    integration.next_sync_allowed_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)

    if integration.sync_error_count >= 5:
        integration.status = "revoked"
        logger.warning(f"Integration {integration.id} marked revoked after {integration.sync_error_count} failures")

    await db.flush()


async def mark_integration_success(
    db: AsyncSession,
    integration: GoogleIntegration,
) -> None:
    integration.last_synced_at = datetime.now(timezone.utc)
    integration.sync_error_count = 0
    integration.next_sync_allowed_at = None
    await db.flush()


async def soft_delete_integration(
    db: AsyncSession,
    integration: GoogleIntegration,
) -> None:
    integration.is_deleted = True
    integration.deleted_at = datetime.now(timezone.utc)
    integration.status = "revoked"
    integration.access_token = None
    integration.refresh_token = None
    await db.flush()
