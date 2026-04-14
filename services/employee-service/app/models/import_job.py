from sqlalchemy import Column, String, Integer, DateTime, UniqueConstraint, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    uploaded_by = Column(UUID(as_uuid=True), nullable=False)

    file_name = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)

    # SHA-256(file_bytes + company_id) — database-level idempotency guard
    idempotency_key = Column(String(64), nullable=False)

    # "v1" — bump when import schema fields change
    schema_version = Column(String(10), nullable=False, default="v1")

    # pending → processing → completed | failed | dry_run
    status = Column(String(20), nullable=False, default="pending", index=True)

    # User-chosen duplicate resolution: skip | update | fail
    duplicate_strategy = Column(String(10), nullable=False, default="update")

    # Row counters — updated by Celery after each 500-row chunk
    total_rows = Column(Integer, nullable=False, default=0)
    succeeded_rows = Column(Integer, nullable=False, default=0)
    failed_rows = Column(Integer, nullable=False, default=0)
    skipped_rows = Column(Integer, nullable=False, default=0)

    # [{row, field, error, suggested_fix, original_value}]
    error_log = Column(JSONB, nullable=True, default=list)

    # [{row, field, original, fixed}]
    auto_corrections = Column(JSONB, nullable=True, default=list)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        # Prevent the same file from being re-processed for the same company
        UniqueConstraint("company_id", "idempotency_key", name="uq_import_jobs_company_idempotency"),
        Index("ix_import_jobs_company_created", "company_id", "created_at"),
    )
