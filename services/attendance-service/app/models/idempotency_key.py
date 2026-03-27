"""Idempotency key storage for safe API retries (multi-tenant).

Stores a mapping of (company_id, key) -> (response_status, response_body)
so that duplicate requests with the same key within a tenant return the
original response without re-executing the operation.

Key design decisions:
- Uniqueness is scoped to (company_id, key), not globally on key alone.
  Two tenants can use the same idempotency key independently.
- A composite index on (company_id, key, request_path, request_method)
  covers the hot lookup path in a single index scan.
- expires_at enables TTL cleanup via a background job.
- Stuck "processing" entries older than PROCESSING_TIMEOUT_MINUTES are
  treated as failed and eligible for retry.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

from app.db.base import Base

PROCESSING_TIMEOUT_MINUTES = 5


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    key = Column(String(255), nullable=False)
    request_path = Column(String(500), nullable=False)
    request_method = Column(String(10), nullable=False)
    request_body_hash = Column(String(64), nullable=True)

    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)

    # processing | completed | error
    status = Column(String(20), nullable=False, default="processing")
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    __table_args__ = (
        # Tenant-scoped uniqueness: same key is allowed across different companies
        UniqueConstraint("company_id", "key", name="uq_idempotency_tenant_key"),
        # Hot-path lookup index: covers the middleware SELECT query
        Index(
            "ix_idempotency_lookup",
            "company_id", "key", "request_path", "request_method",
        ),
        # TTL cleanup index: allows efficient DELETE WHERE expires_at < now()
        Index("ix_idempotency_expires", "expires_at"),
        # Stuck processing recovery: find old "processing" entries quickly
        Index(
            "ix_idempotency_stuck",
            "status", "created_at",
            postgresql_where="status = 'processing'",
        ),
    )
