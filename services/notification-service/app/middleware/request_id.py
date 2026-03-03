import uuid, logging, time
from fastapi import Request, Response

logger = logging.getLogger(__name__)


async def request_id_middleware(request: Request, call_next) -> Response:
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info("Request completed", extra={
        "request_id": request_id, "method": request.method,
        "path": request.url.path, "status_code": response.status_code, "duration_ms": duration_ms,
    })
    return response
