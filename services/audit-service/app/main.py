"""Audit Service — FastAPI Application Entry Point.

Lifespan:
  1. Check DB connectivity (SELECT 1) — no DDL, schema handled by Alembic
  2. Run retention cleanup (delete logs older than LOG_RETENTION_DAYS)
  3. Start RabbitMQ consumer (subscribe to all HRMS events via '#' wildcard)

Startup does NOT create tables — that is Alembic's responsibility.
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.exception_handlers import register_exception_handlers
from app.middleware.request_id import request_id_middleware
from app.db.session import check_db_connectivity, AsyncSessionLocal
from app.events.consumer import AuditEventConsumer
from app.tasks.retention import run_retention_cleanup
from app.services.audit_service import AuditService

configure_logging()
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


async def _audit_service_factory() -> AuditService:
    """Factory used by the consumer: creates a fresh AuditService per message."""
    session = AsyncSessionLocal()
    return AuditService(session)


# Global consumer — referenced by health check endpoint
audit_consumer = AuditEventConsumer(
    rabbitmq_url=settings.RABBITMQ_URL,
    audit_service_factory=_audit_service_factory,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Startup:
      - Verify DB is reachable (no DDL)
      - Run retention cleanup
      - Connect RabbitMQ consumer

    Shutdown:
      - Close RabbitMQ connection
    """
    # 1. DB connectivity check
    db_ok = await check_db_connectivity()
    if db_ok:
        logger.info("Database connectivity verified", extra={"service_task": "startup"})
    else:
        logger.warning(
            "Database unreachable at startup — service may be degraded",
            extra={"service_task": "startup"},
        )

    # 2. Retention cleanup (non-fatal)
    asyncio.create_task(run_retention_cleanup())

    # 3. Start RabbitMQ consumer
    await audit_consumer.connect()

    logger.info("Audit service started", extra={"service_task": "startup"})
    yield

    # Graceful shutdown: allow in-flight requests to complete
    logger.info("Shutting down — waiting for in-flight requests…", extra={"service_task": "shutdown"})
    await asyncio.sleep(5)

    await audit_consumer.close()
    logger.info("Audit service stopped", extra={"service_task": "shutdown"})


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

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Request ID / structured logging middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=request_id_middleware)

# Prometheus instrumentation (exposes /metrics)
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
    logger.info("Prometheus metrics enabled at /metrics")
except ImportError:
    logger.warning("prometheus-fastapi-instrumentator not installed — metrics disabled")

# API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Root health redirect
@app.get("/health", include_in_schema=False)
async def root_health():
    from app.db.session import check_db_connectivity
    db_ok = await check_db_connectivity()
    rabbitmq_ok = (
        audit_consumer._connection is not None
        and not audit_consumer._connection.is_closed
    )
    return {
        "status": "healthy" if (db_ok and rabbitmq_ok) else "degraded",
        "service": "audit-service",
        "version": "1.0.0",
        "checks": {
            "database": "ok" if db_ok else "error",
            "rabbitmq": "ok" if rabbitmq_ok else "error",
        },
    }
