import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.exception_handlers import register_exception_handlers
from app.middleware.request_id import request_id_middleware
from app.events.publisher import EventPublisher

import logging

configure_logging()
logger = logging.getLogger(__name__)

from app.core.rate_limit import limiter
event_publisher = EventPublisher(settings.RABBITMQ_URL)


async def _run_auto_punchout_loop(interval_seconds: int = 300):
    """Background task that auto-closes stale attendance records every N seconds."""
    from app.db.session import AsyncSessionLocal
    from app.scheduler.auto_punchout import auto_close_stale_records

    while True:
        try:
            await asyncio.sleep(interval_seconds)
            async with AsyncSessionLocal() as session:
                closed = await auto_close_stale_records(session, event_publisher)
                if closed:
                    logger.info(f"Auto punch-out: closed {closed} records")
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("Auto punch-out scheduler error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    import redis.asyncio as aioredis
    from app.core.token_blacklist import set_redis

    await event_publisher.connect()
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    set_redis(redis_client)

    # Start auto punch-out scheduler (runs every 5 minutes)
    auto_punchout_task = asyncio.create_task(_run_auto_punchout_loop(300))

    logger.info("Attendance service started", extra={"service_task": "startup"})
    yield

    # Graceful shutdown
    logger.info("Shutting down — waiting for in-flight requests…", extra={"service_task": "shutdown"})
    auto_punchout_task.cancel()
    try:
        await auto_punchout_task
    except asyncio.CancelledError:
        pass
    await asyncio.sleep(5)

    await redis_client.aclose()
    await event_publisher.close()
    logger.info("Attendance service stopped", extra={"service_task": "shutdown"})


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    docs_url=f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
    redoc_url=None,
    lifespan=lifespan,
)

# Generic error envelope handlers (must be registered before rate-limit handler)
register_exception_handlers(app)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

app.add_middleware(BaseHTTPMiddleware, dispatch=request_id_middleware)

@app.get("/health", tags=["health"])
async def health_check():
    """Healthcheck — verifies DB, RabbitMQ, and Redis connectivity."""
    from app.core.token_blacklist import _redis
    from app.db.session import AsyncSessionLocal
    from sqlalchemy import text
    checks = {}
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
    checks["rabbitmq"] = "ok" if (event_publisher._connection and not event_publisher._connection.is_closed) else "error"
    try:
        if _redis:
            await _redis.ping()
        checks["redis"] = "ok" if _redis else "error"
    except Exception:
        checks["redis"] = "error"
    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "healthy" if all_ok else "degraded", "service": "attendance-service", "version": "1.0.0", "checks": checks}


app.include_router(api_router, prefix=settings.API_V1_STR)
