"""
Celery application for the employee service.

Broker  : RabbitMQ (existing RABBITMQ_URL)
Backend : Redis  (existing REDIS_URL, db 1 — separate from JWT blacklist on db 0)

Queues:
  employee_import      — normal import jobs
  employee_import_dlq  — dead-letter; tasks land here after max_retries are exhausted
"""
import os

from celery import Celery

# Read connection strings from env (same vars already used by the FastAPI app)
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
REDIS_URL = os.getenv("REDIS_URL", "redis://hrms-redis:6379/0")
# Use Redis db 1 for Celery results (db 0 is the JWT blacklist)
CELERY_RESULT_BACKEND = REDIS_URL.rstrip("/0") + "/1" if REDIS_URL.endswith("/0") else REDIS_URL + "/1"

celery_app = Celery(
    "employee_service",
    broker=RABBITMQ_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks.import_tasks"],
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Reliability: don't ack until task finishes (prevents loss on worker crash)
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Result expiry: keep task results for 24 h
    result_expires=86400,

    # Routing
    task_routes={
        "app.tasks.import_tasks.process_bulk_import": {"queue": "employee_import"},
    },

    # Dead-letter queue — tasks that exhaust retries are re-queued here
    task_queues={
        "employee_import": {
            "exchange": "employee_import",
            "routing_key": "employee_import",
            "queue_arguments": {
                "x-dead-letter-exchange": "employee_import_dlq",
                "x-dead-letter-routing-key": "employee_import_dlq",
            },
        },
        "employee_import_dlq": {
            "exchange": "employee_import_dlq",
            "routing_key": "employee_import_dlq",
        },
    },

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Suppress CPendingDeprecationWarning in Celery 5.x, forward-compatible with 6.0
    broker_connection_retry_on_startup=True,
)
