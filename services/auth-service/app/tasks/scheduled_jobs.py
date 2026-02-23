"""
Scheduled background tasks for the Auth Service.

Jobs:
- purge_expired_tokens: Deletes expired/revoked refresh tokens (runs every hour)
- purge_expired_magic_tokens: Deletes expired/used magic tokens (runs every 6 hours)
- log_auth_health: Emits a periodic health log entry (runs every 15 minutes)
"""
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.token import RefreshToken
from app.models.magic_token import MagicToken

logger = logging.getLogger(__name__)

# Module-level scheduler instance — started/stopped via FastAPI lifespan
scheduler = AsyncIOScheduler()


async def purge_expired_tokens() -> None:
    """Delete expired or revoked refresh tokens from the database."""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                delete(RefreshToken).where(
                    (RefreshToken.expires_at < datetime.now(timezone.utc).replace(tzinfo=None))
                    | (RefreshToken.revoked == True)  # noqa: E712
                )
            )
            await session.commit()
            deleted_count = result.rowcount
            logger.info(
                "Purged expired/revoked refresh tokens",
                extra={"service_task": "purge_expired_tokens", "deleted_count": deleted_count},
            )
        except Exception:
            logger.exception("Error during token purge", extra={"service_task": "purge_expired_tokens"})
            await session.rollback()


async def purge_expired_magic_tokens() -> None:
    """Delete expired or used magic tokens from the database."""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                delete(MagicToken).where(
                    (MagicToken.expires_at < datetime.now(timezone.utc).replace(tzinfo=None))
                    | (MagicToken.used == True)  # noqa: E712
                )
            )
            await session.commit()
            deleted_count = result.rowcount
            logger.info(
                "Purged expired/used magic tokens",
                extra={"service_task": "purge_expired_magic_tokens", "deleted_count": deleted_count},
            )
        except Exception:
            logger.exception("Error during magic token purge", extra={"service_task": "purge_expired_magic_tokens"})
            await session.rollback()


async def log_auth_health() -> None:
    """Emit a periodic health-check log for uptime monitoring."""
    logger.info(
        "Auth service health ping",
        extra={"service_task": "log_auth_health", "status": "healthy"},
    )


def create_scheduler() -> AsyncIOScheduler:
    """Register all jobs and return the scheduler (not yet started)."""

    # Purge expired refresh tokens every hour
    scheduler.add_job(
        purge_expired_tokens,
        trigger=IntervalTrigger(hours=1),
        id="purge_expired_tokens",
        name="Purge Expired Refresh Tokens",
        replace_existing=True,
    )

    # Purge expired magic tokens every 6 hours
    scheduler.add_job(
        purge_expired_magic_tokens,
        trigger=IntervalTrigger(hours=6),
        id="purge_expired_magic_tokens",
        name="Purge Expired Magic Tokens",
        replace_existing=True,
    )

    # Health ping every 15 minutes
    scheduler.add_job(
        log_auth_health,
        trigger=IntervalTrigger(minutes=15),
        id="log_auth_health",
        name="Auth Health Ping",
        replace_existing=True,
    )

    logger.info("Scheduler configured with %d jobs", len(scheduler.get_jobs()))
    return scheduler
