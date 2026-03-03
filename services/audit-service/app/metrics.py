"""Prometheus counters and gauges for the Audit Service."""
try:
    from prometheus_client import Counter, Gauge

    COUNTERS = {
        "events_processed_total": Counter(
            "audit_events_processed_total",
            "Total number of events successfully recorded",
        ),
        "events_failed_total": Counter(
            "audit_events_failed_total",
            "Total number of events rejected to DLQ",
        ),
        "events_duplicate_total": Counter(
            "audit_events_duplicate_total",
            "Total number of duplicate events skipped (idempotency)",
        ),
    }

    GAUGES = {
        "dlq_count": Gauge(
            "audit_dlq_count",
            "Approximate number of messages in the audit dead-letter queue",
        ),
    }

except ImportError:
    # prometheus_client not installed — metrics disabled gracefully
    COUNTERS = {}
    GAUGES = {}
