import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    """Dependency that provides an async DB session per request."""
    async with AsyncSessionLocal() as session:
        yield session


async def check_db_connectivity() -> bool:
    """Ping the database. Returns True if healthy, False otherwise.

    Used by the health check endpoint and startup lifespan check.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error(
            f"Database connectivity check failed: {exc}",
            extra={"service_task": "db_health"},
        )
        return False
