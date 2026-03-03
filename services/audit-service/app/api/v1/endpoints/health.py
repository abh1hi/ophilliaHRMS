from fastapi import APIRouter
from app.db.session import check_db_connectivity

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Health check endpoint.

    Checks:
    - DB connectivity (SELECT 1)
    - RabbitMQ status (via global consumer connection)

    Returns 200 with component statuses.
    """
    db_ok = await check_db_connectivity()

    # Check RabbitMQ via global consumer reference
    rabbitmq_ok = False
    try:
        from app.main import audit_consumer
        rabbitmq_ok = (
            audit_consumer._connection is not None
            and not audit_consumer._connection.is_closed
        )
    except Exception:
        rabbitmq_ok = False

    overall = "healthy" if (db_ok and rabbitmq_ok) else "degraded"

    return {
        "status": overall,
        "service": "audit-service",
        "version": "1.0.0",
        "checks": {
            "database": "ok" if db_ok else "error",
            "rabbitmq": "ok" if rabbitmq_ok else "error",
        },
    }
