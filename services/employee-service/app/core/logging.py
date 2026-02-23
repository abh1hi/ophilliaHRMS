import logging
import json
from datetime import datetime, timezone

# Extra fields from the HRMS Logging & Observability standard
_STANDARD_EXTRA_FIELDS = (
    "request_id",
    "user_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "service_task",
)


class JSONFormatter(logging.Formatter):
    """Structured JSON formatter for centralized log aggregation (ELK/Loki).

    Follows the HRMS Logging & Observability Standard:
    - timestamp, level, service_name, message, logger are mandatory.
    - request_id, user_id, method, path, status_code, duration_ms are optional.
    - Exceptions are serialized as 'exception'.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service_name": "employee-service",
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach any extra fields passed via `extra={...}` in the log call
        for field in _STANDARD_EXTRA_FIELDS:
            if hasattr(record, field):
                log_record[field] = getattr(record, field)

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logger with structured JSON output.

    Call once at application startup (in main.py).
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    # Replace any default handlers to avoid duplicate / unformatted output
    root_logger.handlers = [handler]

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
