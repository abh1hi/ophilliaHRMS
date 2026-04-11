import uuid
import logging
import time
from contextvars import ContextVar
from fastapi import Request, Response

logger = logging.getLogger(__name__)

# ContextVar holding the correlation ID for the current request.
# Onboarding publisher reads this to propagate correlation across service boundaries.
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


async def request_id_middleware(request: Request, call_next) -> Response:
    # Propagate upstream X-Request-ID; generate new if absent
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    token = correlation_id_var.set(correlation_id)

    start = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        correlation_id_var.reset(token)

    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Correlation-ID"] = correlation_id
    logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response
