import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSON, UUID

from app.db.base import Base


def naive_utcnow():
    """Return current UTC time tz-naive (SQLAlchemy DateTime requires this)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuditLog(Base):
    """Immutable audit log row. Insert-only — no updates or deletes ever."""

    __tablename__ = "audit_logs"

    # ── Primary key ───────────────────────────────────────────────────────────
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ── Event identity ────────────────────────────────────────────────────────
    event_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    event_version = Column(Integer, nullable=False, default=1)
    event_type = Column(String(100), nullable=False, index=True)
    service_source = Column(String(100), nullable=False, index=True)

    # ── Tenant + actor ────────────────────────────────────────────────────────
    # company_id inherited from Base (already indexed)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # ── Distributed tracing ───────────────────────────────────────────────────
    correlation_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # ── Forensic / request metadata ──────────────────────────────────────────
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    http_method = Column(String(10), nullable=True)
    endpoint = Column(String(255), nullable=True)

    # ── Event payload (sanitized — no secrets) ───────────────────────────────
    payload = Column(JSON, nullable=False, default=dict)

    # ── Timestamps ───────────────────────────────────────────────────────────
    timestamp = Column(DateTime, nullable=False, index=True, default=naive_utcnow)
    created_at = Column(DateTime, nullable=False, default=naive_utcnow)

    # ── Composite indexes (critical for multi-tenant query performance) ───────
    __table_args__ = (
        # Most common query pattern: recent events for a tenant
        Index("idx_company_timestamp", "company_id", "timestamp"),
        # Filter by event type within a tenant
        Index("idx_company_event_type", "company_id", "event_type"),
        # Filter by actor within a tenant
        Index("idx_company_user", "company_id", "user_id"),
        # Correlation ID lookup (distributed tracing)
        Index("idx_correlation_id", "correlation_id"),
        # Partial index: recent 90 days — most queries hit recent data
        Index(
            "idx_recent_logs",
            "timestamp",
            postgresql_where=text("timestamp > now() - interval '90 days'"),
        ),
    )
