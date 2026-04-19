from sqlalchemy import Column, String, Float, Integer, Time, Date, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PolicyException(Base):
    """Temporary override of a specific employee's attendance policy.

    Takes precedence over all normal policy resolution (employee → department →
    global) for the duration of the exception window.

    Use cases: medical leave (different check-in method), remote work
    (different geofence / no geofence), special project (different work hours).
    """
    __tablename__ = "policy_exceptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    reason = Column(String(500), nullable=False)
    reason_category = Column(String(50), nullable=True)  # medical_leave | client_visit | training | custom

    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=True)

    # Override fields — null means "inherit from the underlying policy"
    override_method = Column(String(20), nullable=True)
    override_work_hours = Column(Float, nullable=True)
    override_work_start_time = Column(Time, nullable=True)
    override_late_grace_minutes = Column(Integer, nullable=True)

    # Single geofence override (kept for backward compat; superseded by override_geofence_ids)
    override_geofence_id = Column(
        UUID(as_uuid=True),
        ForeignKey("geofence_locations.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Multi-geofence override: list of UUID strings — replaces all policy geofences during exception
    override_geofence_ids = Column(JSONB, nullable=True)

    # Overtime policy override for this exception window
    override_overtime_policy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("overtime_policies.id", ondelete="SET NULL"),
        nullable=True,
    )

    approved_by = Column(UUID(as_uuid=True), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=naive_utcnow,
        onupdate=naive_utcnow,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_policy_exception_employee_id", "employee_id"),
        Index("ix_policy_exception_company_id", "company_id"),
        Index("ix_policy_exception_dates", "from_date", "to_date"),
        Index("ix_exception_employee_dates", "employee_id", "from_date", "to_date"),
    )
