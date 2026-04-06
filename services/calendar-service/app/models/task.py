import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from sqlalchemy.types import UserDefinedType

from app.db.base import Base


class TSVECTOR(UserDefinedType):
    cache_ok = True

    def get_col_spec(self, **kw):
        return "TSVECTOR"


class CalendarTask(Base):
    __tablename__ = "calendar_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("calendar_events.id", ondelete="SET NULL"), nullable=True)
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey("calendar_tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(30), default="todo", nullable=False, index=True)
    priority = Column(String(20), default="medium", nullable=False, index=True)
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    google_tasklist_id = Column(String(300), nullable=True)
    google_task_id = Column(String(300), nullable=True, index=True)
    tags = Column(JSONB, default=list, nullable=False)
    attachments = Column(JSONB, default=list, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    search_vector = Column(TSVECTOR, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    workspace = relationship("Workspace", back_populates="tasks")
    assignees = relationship("TaskAssignee", back_populates="task", lazy="select")
    comments = relationship("TaskComment", back_populates="task", lazy="select")
    subtasks = relationship("CalendarTask", lazy="select")
