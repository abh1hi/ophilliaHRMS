"""Calendar Service — FastAPI Application Entry Point."""
import asyncio
import logging
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
from app.db.session import engine

configure_logging()
logger = logging.getLogger(__name__)

from app.core.rate_limit import limiter

event_publisher = EventPublisher(settings.RABBITMQ_URL)


async def _run_google_sync_loop(interval_seconds: int = 300):
    """Background task: sync Google Calendar for all active integrations every N seconds."""
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            # Lazy import to avoid circular deps at startup
            from app.db.session import AsyncSessionLocal
            from app.repositories.google_repository import list_active_integrations
            async with AsyncSessionLocal() as session:
                integrations = await list_active_integrations(session)
                logger.info(f"Google sync: checking {len(integrations)} integrations")
                # Phase 3: actual sync logic will be in google_calendar_sync.py
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("Google sync scheduler error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    import redis.asyncio as aioredis
    from app.core.token_blacklist import set_redis
    from app.core.cache import set_cache_redis
    from sqlalchemy import text

    await event_publisher.connect()

    # Verify DB connectivity
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connectivity verified", extra={"service_task": "startup"})
    except Exception as exc:
        logger.warning(f"Database unreachable at startup: {exc}", extra={"service_task": "startup"})

    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    set_redis(redis_client)
    set_cache_redis(redis_client)

    # Start background schedulers
    google_sync_task = asyncio.create_task(
        _run_google_sync_loop(settings.GOOGLE_SYNC_INTERVAL_SECONDS)
    )

    logger.info("Calendar service started", extra={"service_task": "startup"})
    yield

    # Graceful shutdown
    logger.info("Shutting down — waiting for in-flight requests…", extra={"service_task": "shutdown"})
    google_sync_task.cancel()
    try:
        await google_sync_task
    except asyncio.CancelledError:
        pass
    await asyncio.sleep(5)
    await redis_client.aclose()
    await event_publisher.close()
    logger.info("Calendar service stopped", extra={"service_task": "shutdown"})


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

# Middleware: innermost first (CORS must be outermost → registered last)
app.add_middleware(BaseHTTPMiddleware, dispatch=request_id_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
except ImportError:
    pass

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", include_in_schema=False)
async def health_check():
    """Healthcheck — verifies DB, RabbitMQ, and Redis connectivity."""
    from sqlalchemy import text
    from app.core.token_blacklist import _redis
    checks = {}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
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
    return {
        "status": "healthy" if all_ok else "degraded",
        "service": "calendar-service",
        "version": "1.0.0",
        "checks": checks,
    }
