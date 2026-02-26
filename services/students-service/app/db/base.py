from sqlalchemy.orm import DeclarativeBase, MappedColumn
from sqlalchemy import MetaData, Column
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Consistent naming convention for Alembic auto-generation
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    company_id = Column(UUID(as_uuid=True), index=True, nullable=False, default=uuid.uuid4)
