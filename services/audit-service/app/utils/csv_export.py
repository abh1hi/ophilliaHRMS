"""CSV streaming export for audit logs."""
import csv
import io
from typing import AsyncGenerator

from app.models.audit_log import AuditLog


EXPORT_COLUMNS = [
    "id",
    "event_id",
    "event_version",
    "event_type",
    "service_source",
    "company_id",
    "user_id",
    "correlation_id",
    "ip_address",
    "user_agent",
    "http_method",
    "endpoint",
    "timestamp",
    "created_at",
]


def audit_logs_to_csv(logs: list[AuditLog]) -> str:
    """Convert a list of AuditLog ORM objects to a CSV string.

    Payload is intentionally excluded from CSV exports — it may still
    contain large JSON blobs. Users needing payload data should use
    the JSON API endpoint.
    """
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=EXPORT_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for log in logs:
        writer.writerow(
            {col: getattr(log, col, "") for col in EXPORT_COLUMNS}
        )
    return output.getvalue()
