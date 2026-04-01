"""Payroll Service — FastAPI Application Entry Point."""
import asyncio, logging
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
from app.db.session import check_db_connectivity
from app.events.consumer import start_consumer

configure_logging()
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import redis.asyncio as aioredis
    from app.core.token_blacklist import set_redis

    db_ok = await check_db_connectivity()
    if db_ok:
        logger.info("Database connectivity verified", extra={"service_task": "startup"})
    else:
        logger.warning("Database unreachable at startup", extra={"service_task": "startup"})

    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    set_redis(redis_client)
    consumer_task = asyncio.create_task(start_consumer())
    logger.info("Payroll service started", extra={"service_task": "startup"})
    yield

    # Graceful shutdown: allow in-flight requests to complete
    logger.info("Shutting down — waiting for in-flight requests…", extra={"service_task": "shutdown"})
    await asyncio.sleep(5)

    await redis_client.aclose()
    consumer_task.cancel()
    logger.info("Payroll service stopped", extra={"service_task": "shutdown"})


app = FastAPI(
    title=settings.PROJECT_NAME, version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    docs_url=f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
    redoc_url=None,
    lifespan=lifespan,
)

# Generic error envelope handlers (must be registered before rate-limit handler)
register_exception_handlers(app)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(CORSMiddleware, allow_origins=settings.ALLOWED_ORIGINS, allow_credentials=True, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"], allow_headers=["*"])
app.add_middleware(BaseHTTPMiddleware, dispatch=request_id_middleware)

try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
except ImportError:
    pass

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", include_in_schema=False)
async def root_health():
    """Healthcheck — verifies DB and Redis connectivity."""
    from app.core.token_blacklist import _redis
    checks = {}
    checks["database"] = "ok" if await check_db_connectivity() else "error"
    try:
        if _redis:
            await _redis.ping()
        checks["redis"] = "ok" if _redis else "error"
    except Exception:
        checks["redis"] = "error"
    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "healthy" if all_ok else "degraded", "service": "payroll-service", "version": "1.0.0", "checks": checks}
