import logging
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session, with_loader_criteria

from app.core.config import settings
from app.db.base import Base

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db(company_id: str = None):
    async with AsyncSessionLocal() as session:
        if company_id:
            session.info["company_id"] = company_id
        yield session


async def check_db_connectivity() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error(f"DB connectivity check failed: {exc}", extra={"service_task": "db_health"})
        return False


@event.listens_for(Session, "do_orm_execute")
def _add_tenant_filter(execute_state):
    if execute_state.is_select and not execute_state.is_column_load and not execute_state.is_relationship_load:
        company_id = execute_state.session.info.get("company_id")
        if company_id:
            execute_state.statement = execute_state.statement.options(
                with_loader_criteria(Base, lambda cls: cls.company_id == company_id, include_aliases=True)
            )


@event.listens_for(Session, "before_flush")
def _set_company_id(session, flush_context, instances):
    company_id = session.info.get("company_id")
    if not company_id:
        return
    for obj in session.new:
        if hasattr(obj, "company_id") and getattr(obj, "company_id") is None:
            setattr(obj, "company_id", company_id)
