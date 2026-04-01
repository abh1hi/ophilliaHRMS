from sqlalchemy import Column, String, Float, Time, Boolean, Integer, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, time, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PolicyTemplate(Base):
    """Reusable policy template that can be applied to any department.

    Mirrors AttendancePolicy fields but is not directly used in policy
    resolution — it is a blueprint to stamp out real policies.
    """
    __tablename__ = "policy_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)

    # Policy settings (mirrors AttendancePolicy)
    method = Column(String(20), nullable=False, default="manual")

    # Intentionally no FK — templates survive geofence deletions
    geofence_id = Column(UUID(as_uuid=True), nullable=True)

    work_start_time = Column(Time, nullable=True, default=time(9, 0))
    work_hours_per_day = Column(Float, nullable=False, default=8.0)
    auto_close_time = Column(Time, nullable=True, default=time(23, 59))
    task_planning_grace_minutes = Column(Float, nullable=False, default=30.0)
    allow_night_shift = Column(String(10), nullable=False, default="false")
    max_shifts_per_day = Column(Float, nullable=False, default=2)
    late_grace_period_minutes = Column(Integer, nullable=False, default=0)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=naive_utcnow,
        onupdate=naive_utcnow,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_policy_template_company_id", "company_id"),
        Index("ix_policy_template_name", "name"),
    )
