from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase
import uuid

class Base(DeclarativeBase):
    company_id = Column(UUID(as_uuid=True), index=True, nullable=False, default=uuid.uuid4)
