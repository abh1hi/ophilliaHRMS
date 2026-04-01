import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.exception_handlers import register_exception_handlers
from app.middleware.request_id import request_id_middleware
from app.events.publisher import EventPublisher
from app.db.session import get_db

import logging

configure_logging()
logger = logging.getLogger(__name__)

# Rate limiter (shared module — importable by endpoint files)
from app.core.rate_limit import limiter

# Event publisher (global, shared across request lifecycle)
event_publisher = EventPublisher(settings.RABBITMQ_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: connect to RabbitMQ and Redis on startup, close on shutdown."""
    import redis.asyncio as aioredis
    from app.core.token_blacklist import set_redis

    await event_publisher.connect()
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    set_redis(redis_client)
    logger.info("Employee service started", extra={"service_task": "startup"})
    yield

    # Graceful shutdown: allow in-flight requests to complete
    logger.info("Shutting down — waiting for in-flight requests…", extra={"service_task": "shutdown"})
    await asyncio.sleep(5)

    await redis_client.aclose()
    await event_publisher.close()
    logger.info("Employee service stopped", extra={"service_task": "shutdown"})


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
    redoc_url=None,
    lifespan=lifespan,
)

# Generic error envelope handlers (must be registered before rate-limit handler)
register_exception_handlers(app)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — explicit methods/headers (no wildcard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Request ID / structured logging middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=request_id_middleware)

# API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Healthcheck — verifies DB, RabbitMQ, and Redis connectivity."""
    from app.core.token_blacklist import _redis
    checks = {}
    try:
        await db.execute(text("SELECT 1"))
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
    return {"status": "healthy" if all_ok else "degraded", "service": "employee-service", "version": "1.0.0", "checks": checks}
