import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.exception_handlers import register_exception_handlers
from app.middleware.request_id import request_id_middleware
from app.events.publisher import EventPublisher
from app.events.consumer import OnboardingEventConsumer
from app.db.session import get_db, AsyncSessionLocal

import logging

configure_logging()
logger = logging.getLogger(__name__)

event_publisher = EventPublisher(settings.RABBITMQ_URL)


async def _onboarding_service_factory():
    """Create an OnboardingService with its own DB session for event processing."""
    from app.services.onboarding_service import OnboardingService
    session = AsyncSessionLocal()
    try:
        return OnboardingService(session)
    except Exception:
        await session.close()
        raise


event_consumer = OnboardingEventConsumer(settings.RABBITMQ_URL, _onboarding_service_factory)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: connect to RabbitMQ on startup, close on shutdown."""
    await event_publisher.connect()
    app.state.event_publisher = event_publisher

    # Seed templates on startup
    from app.seeds.loader import seed_templates
    async with AsyncSessionLocal() as db:
        await seed_templates(db)

    # Start event consumer in background
    asyncio.create_task(event_consumer.connect())

    logger.info("Onboarding service started", extra={"service_task": "startup"})
    yield

    logger.info("Shutting down — waiting for in-flight requests…", extra={"service_task": "shutdown"})
    await asyncio.sleep(3)

    await event_consumer.close()
    await event_publisher.close()
    logger.info("Onboarding service stopped", extra={"service_task": "shutdown"})


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
    redoc_url=None,
    lifespan=lifespan,
)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

app.add_middleware(BaseHTTPMiddleware, dispatch=request_id_middleware)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Healthcheck — verifies DB and RabbitMQ connectivity."""
    checks = {}
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
    checks["rabbitmq"] = "ok" if (event_publisher._connection and not event_publisher._connection.is_closed) else "error"
    all_ok = all(v == "ok" for v in checks.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "service": "onboarding-service",
        "version": "1.0.0",
        "checks": checks,
    }


@app.get("/health/ready", tags=["health"])
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness probe — verifies DB, RabbitMQ, and migrations are applied."""
    checks = {}

    # Database connectivity
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"

    # Migrations applied (check if onboarding_status table exists)
    try:
        await db.execute(text("SELECT 1 FROM onboarding_status LIMIT 1"))
        checks["migrations"] = "ok"
    except Exception:
        checks["migrations"] = "error"

    # RabbitMQ
    checks["rabbitmq"] = "ok" if (event_publisher._connection and not event_publisher._connection.is_closed) else "error"

    # Templates seeded
    try:
        from app.models.onboarding import OnboardingTemplate
        from sqlalchemy import select, func
        result = await db.execute(select(func.count()).select_from(OnboardingTemplate))
        template_count = result.scalar() or 0
        checks["templates"] = "ok" if template_count > 0 else "warning"
    except Exception:
        checks["templates"] = "error"

    all_ok = all(v == "ok" for v in checks.values())
    status_code = 200 if all_ok else 503
    from starlette.responses import JSONResponse
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_ok else "not_ready",
            "service": "onboarding-service",
            "version": "1.0.0",
            "checks": checks,
        },
    )
