import asyncio
import logging

from app.db.session import engine
from app.db.base import Base
from app.models import user, token, magic_token  # noqa: F401

logger = logging.getLogger(__name__)


async def create_tables():
    """Create all tables. In production use Alembic migrations instead."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created (dev only — use Alembic in production)")


if __name__ == "__main__":
    asyncio.run(create_tables())
