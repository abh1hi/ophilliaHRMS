"""
Generic FastAPI exception handlers for the employee-service.

All error responses are normalised to the OphilliaHRMS API contract envelope:
    {
        "success": false,
        "data": null,
        "error": { "code": "<ERROR_CODE>", "message": "<human-readable message>" }
    }

Register by calling ``register_exception_handlers(app)`` in main.py.
"""
import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

_STATUS_CODE_MAP: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMIT_EXCEEDED",
    500: "INTERNAL_SERVER_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "meta": None,
            "error": {"code": code, "message": message},
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = _STATUS_CODE_MAP.get(exc.status_code, "HTTP_ERROR")
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    logger.warning(
        "HTTPException",
        extra={"status_code": exc.status_code, "code": code, "path": str(request.url)},
    )
    return _error_response(exc.status_code, code, message)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    field_messages = []
    for err in errors:
        loc = " → ".join(str(p) for p in err.get("loc", []) if p != "body")
        msg = err.get("msg", "invalid value")
        field_messages.append(f"{loc}: {msg}" if loc else msg)
    message = "; ".join(field_messages) if field_messages else "Validation failed"
    logger.warning("ValidationError", extra={"path": str(request.url), "errors": errors})
    return _error_response(422, "VALIDATION_ERROR", message)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception", exc_info=exc, extra={"path": str(request.url)})
    return _error_response(500, "INTERNAL_SERVER_ERROR", "An unexpected error occurred")


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all generic exception handlers to *app*."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)  # type: ignore[arg-type]
