import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from sqlalchemy.types import UserDefinedType

from app.db.base import Base


class TSVECTOR(UserDefinedType):
    cache_ok = True

    def get_col_spec(self, **kw):
        return "TSVECTOR"


class TaskComment(Base):
    __tablename__ = "task_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("calendar_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("task_comments.id", ondelete="CASCADE"), nullable=True, index=True)
    body = Column(Text, nullable=False)
    search_vector = Column(TSVECTOR, nullable=True)
    status = Column(String(20), default="active", nullable=False)
    edited_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    task = relationship("CalendarTask", back_populates="comments")
    replies = relationship("TaskComment", lazy="select")
