import logging
from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogFilter

logger = logging.getLogger(__name__)


class AuditLogRepository:
    """Data access layer for audit_logs.

    INSERT-ONLY. No update or delete methods exist by design.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> AuditLog:
        """Insert a new audit log entry. Raises on constraint violations."""
        log = AuditLog(**data)
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def exists(self, event_id: UUID) -> bool:
        """Check whether an event_id already exists (idempotency gate)."""
        result = await self.db.execute(
            select(AuditLog.id).where(AuditLog.event_id == event_id).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def get_by_id(self, log_id: UUID) -> Optional[AuditLog]:
        result = await self.db.execute(
            select(AuditLog).where(AuditLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def list_logs(self, filters: AuditLogFilter) -> list[AuditLog]:
        """Return paginated, filtered audit logs."""
        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc())
        stmt = self._apply_filters(stmt, filters)
        stmt = stmt.offset(filters.skip).limit(filters.limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_logs(self, filters: AuditLogFilter) -> int:
        """Return total count matching the given filters."""
        stmt = select(func.count(AuditLog.id))
        stmt = self._apply_filters(stmt, filters)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def delete_older_than(self, cutoff: datetime) -> int:
        """Delete rows older than `cutoff`. Used by the retention task."""
        from sqlalchemy import delete
        result = await self.db.execute(
            delete(AuditLog).where(AuditLog.created_at < cutoff)
        )
        await self.db.commit()
        return result.rowcount

    # ── Private helpers ────────────────────────────────────────────────────────

    def _apply_filters(self, stmt, filters: AuditLogFilter):
        conditions = []
        if filters.event_type:
            conditions.append(AuditLog.event_type == filters.event_type)
        if filters.service_source:
            conditions.append(AuditLog.service_source == filters.service_source)
        if filters.user_id:
            conditions.append(AuditLog.user_id == filters.user_id)
        if filters.company_id:
            conditions.append(AuditLog.company_id == filters.company_id)
        if filters.correlation_id:
            conditions.append(AuditLog.correlation_id == filters.correlation_id)
        if filters.date_from:
            conditions.append(AuditLog.timestamp >= filters.date_from)
        if filters.date_to:
            conditions.append(AuditLog.timestamp <= filters.date_to)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        return stmt
