import uuid
import logging
from starlette.requests import Request

logger = logging.getLogger(__name__)


async def request_id_middleware(request: Request, call_next):
    """Attach X-Request-ID to every request and propagate it in logs."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    # Store on request state for use anywhere in the request lifecycle
    request.state.request_id = request_id

    # Bind request_id into the logger for this request scope
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id
        return record

    logging.setLogRecordFactory(record_factory)
    try:
        response = await call_next(request)
    finally:
        logging.setLogRecordFactory(old_factory)

    response.headers["X-Request-ID"] = request_id
    return response
