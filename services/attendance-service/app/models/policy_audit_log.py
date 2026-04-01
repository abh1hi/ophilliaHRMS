from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PolicyAuditLog(Base):
    """Immutable audit trail for every create/update/delete on AttendancePolicy.

    No FK on policy_id intentionally — log entries survive policy deletion.
    """
    __tablename__ = "policy_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # References the policy — no FK so the log survives deletion
    policy_id = Column(UUID(as_uuid=True), nullable=False)

    action = Column(String(20), nullable=False)  # created | updated | deleted
    changed_by = Column(UUID(as_uuid=True), nullable=False)  # user_id who made the change
    timestamp = Column(DateTime, nullable=False, default=naive_utcnow)

    # Full policy snapshot before and after the change
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_policy_audit_policy_id", "policy_id"),
        Index("ix_policy_audit_company_id", "company_id"),
        Index("ix_policy_audit_timestamp", "timestamp"),
    )
