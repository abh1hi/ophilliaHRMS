from sqlalchemy import Column, String, Float, Date, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
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

    reason = Column(String(500), nullable=False)  # medical | personal | project | other

    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=True)  # null = indefinite / open-ended

    # Override fields — null means "use whatever the policy says"
    override_method = Column(String(20), nullable=True)       # manual | geofence | both
    override_work_hours = Column(Float, nullable=True)         # e.g. 6.0 for reduced hours

    # If set, use this geofence instead of the policy's geofence (SET NULL on delete)
    override_geofence_id = Column(
        UUID(as_uuid=True),
        ForeignKey("geofence_locations.id", ondelete="SET NULL"),
        nullable=True,
    )

    approved_by = Column(UUID(as_uuid=True), nullable=False)  # user_id of approver
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
    )
