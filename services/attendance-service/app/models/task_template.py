from sqlalchemy import Column, String, Text, Numeric, DateTime, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TaskTemplate(Base):
    """Reusable task template for quick-add functionality.

    Templates can be created by employees (personal) or by admins (shared).
    """

    __tablename__ = "task_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Owner: if set, template is personal; if null, it's shared (company-wide)
    created_by = Column(UUID(as_uuid=True), nullable=True, index=True)

    title = Column(String(200), nullable=False)
    details = Column(Text, nullable=True)
    estimated_finish_time = Column(String(20), nullable=True)
    expected_expenses = Column(Numeric(10, 2), nullable=True)

    is_shared = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=naive_utcnow,
        onupdate=naive_utcnow,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_template_company", "company_id"),
        Index("ix_template_created_by", "created_by"),
    )
