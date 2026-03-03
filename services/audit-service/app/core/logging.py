import logging
import json
from datetime import datetime, timezone

_STANDARD_EXTRA_FIELDS = (
    "request_id",
    "user_id",
    "company_id",
    "event_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "service_task",
)


class JSONFormatter(logging.Formatter):
    """Structured JSON formatter for centralized log aggregation (ELK/Loki).

    Mandatory fields: timestamp, level, service_name, message, logger.
    Optional fields: request_id, user_id, company_id, event_id, method,
                     path, status_code, duration_ms, service_task.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service_name": "audit-service",
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field in _STANDARD_EXTRA_FIELDS:
            if hasattr(record, field):
                log_record[field] = getattr(record, field)

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logger with structured JSON output.

    Call once at application startup from main.py.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("aio_pika").setLevel(logging.WARNING)
