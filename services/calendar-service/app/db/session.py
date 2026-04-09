from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, with_loader_criteria

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,
    connect_args={"timeout": 10},
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db(company_id: str = None):
    async with AsyncSessionLocal() as session:
        if company_id:
            session.info["company_id"] = company_id
        yield session


from sqlalchemy.orm import Session
from app.db.base import Base


@event.listens_for(Session, "do_orm_execute")
def _add_tenant_filter(execute_state):
    """Intercepts ORM queries and adds a global filter for company_id."""
    if (
        execute_state.is_select
        and not execute_state.is_column_load
        and not execute_state.is_relationship_load
    ):
        company_id = execute_state.session.info.get("company_id")
        if company_id:
            execute_state.statement = execute_state.statement.options(
                with_loader_criteria(
                    Base,
                    lambda cls: cls.company_id == company_id,
                    include_aliases=True,
                )
            )


@event.listens_for(Session, "before_flush")
def _set_company_id(session, flush_context, instances):
    """Automatically sets company_id on new objects if present in session.info."""
    company_id = session.info.get("company_id")
    if not company_id:
        return
    for obj in session.new:
        if hasattr(obj, "company_id") and getattr(obj, "company_id") is None:
            setattr(obj, "company_id", company_id)
