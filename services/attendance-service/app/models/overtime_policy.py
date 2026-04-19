from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class OvertimePolicy(Base):
    """Overtime thresholds and multipliers per jurisdiction.

    Resolution hierarchy mirrors AttendancePolicy:
      employee → location → department → company-global
    """
    __tablename__ = "overtime_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Scope — same hierarchy as AttendancePolicy
    employee_id = Column(UUID(as_uuid=True), nullable=True)
    department_id = Column(UUID(as_uuid=True), nullable=True)
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("geofence_locations.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Compliance jurisdiction
    jurisdiction = Column(String(20), nullable=False, default="CUSTOM")  # INDIA | EU | CUSTOM
    compliance_profile = Column(String(100), nullable=True)  # e.g. INDIA_FACTORIES_ACT

    # Thresholds (hours)
    daily_ot_threshold_hours = Column(Float, nullable=False, default=8.0)
    weekly_ot_threshold_hours = Column(Float, nullable=False, default=40.0)
    max_daily_hours = Column(Float, nullable=False, default=12.0)

    # Multipliers
    daily_ot_multiplier = Column(Float, nullable=False, default=1.5)
    weekly_ot_multiplier = Column(Float, nullable=False, default=1.5)
    weekend_multiplier = Column(Float, nullable=False, default=1.5)
    holiday_multiplier = Column(Float, nullable=False, default=2.0)

    # Comp-off vs cash
    prefer_comp_off = Column(Boolean, nullable=False, default=False)
    comp_off_ratio = Column(Float, nullable=False, default=1.0)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_ot_policy_employee", "employee_id"),
        Index("ix_ot_policy_department", "department_id"),
        Index("ix_ot_policy_location", "location_id"),
        Index("ix_ot_policy_scope_lookup", "company_id", "employee_id", "location_id", "department_id"),
    )


class OvertimePolicyAudit(Base):
    """Audit trail for OvertimePolicy changes."""
    __tablename__ = "overtime_policy_audit"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    policy_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # no FK — survives policy deletion
    action = Column(String(20), nullable=False)  # created | updated | deleted
    changed_by = Column(UUID(as_uuid=True), nullable=False)
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    timestamp = Column(DateTime, default=naive_utcnow, nullable=False)
