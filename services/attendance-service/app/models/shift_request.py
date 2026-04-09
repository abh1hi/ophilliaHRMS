from sqlalchemy import Column, String, DateTime, Integer, Date, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ShiftRequest(Base):
    __tablename__ = "shift_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    request_type = Column(String(20), nullable=False)  # swap | change | leave
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    requested_shift_type_id = Column(UUID(as_uuid=True), nullable=True)
    reason = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending | approved | rejected | cancelled
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_note = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    __table_args__ = (
        Index("ix_shift_requests_employee_status", "company_id", "employee_id", "status"),
    )
