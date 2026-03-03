from fastapi import APIRouter
from app.db.session import check_db_connectivity

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    db_ok = await check_db_connectivity()
    return {
        "status": "healthy" if db_ok else "degraded",
        "service": "payroll-service",
        "version": "1.0.0",
        "checks": {"database": "ok" if db_ok else "error"},
    }
