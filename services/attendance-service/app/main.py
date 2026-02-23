from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler, Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.middleware.request_id import request_id_middleware
from app.events.publisher import EventPublisher

import logging

configure_logging()
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
event_publisher = EventPublisher(settings.RABBITMQ_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await event_publisher.connect()
    logger.info("Attendance service started", extra={"service_task": "startup"})
    yield
    await event_publisher.close()
    logger.info("Attendance service stopped", extra={"service_task": "shutdown"})


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(BaseHTTPMiddleware, dispatch=request_id_middleware)

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "service": "attendance-service", "version": "1.0.0"}


app.include_router(api_router, prefix=settings.API_V1_STR)
