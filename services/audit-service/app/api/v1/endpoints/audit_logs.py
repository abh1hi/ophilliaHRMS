import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_audit_service, require_hr_or_admin, require_super_admin
from app.schemas.audit_log import AuditLogFilter, AuditLogListResponse, AuditLogResponse
from app.services.audit_service import AuditService
from app.utils.csv_export import audit_logs_to_csv
from app.repositories.audit_log_repository import AuditLogRepository

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get(
    "/logs",
    response_model=AuditLogListResponse,
    summary="List audit logs",
    description="Paginated, filtered audit log listing. Requires HR or Admin role.",
)
async def list_audit_logs(
    request: Request,
    event_type: Optional[str] = Query(None, description="e.g. employee.created"),
    service_source: Optional[str] = Query(None),
    user_id: Optional[UUID] = Query(None),
    company_id: Optional[UUID] = Query(None),
    correlation_id: Optional[UUID] = Query(None),
    date_from: Optional[str] = Query(None, description="ISO-8601 datetime"),
    date_to: Optional[str] = Query(None, description="ISO-8601 datetime"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    _user: dict = Depends(require_hr_or_admin),
    service: AuditService = Depends(get_audit_service),
):
    from datetime import datetime

    def _parse_dt(s):
        try:
            return datetime.fromisoformat(s) if s else None
        except ValueError:
            return None

    filters = AuditLogFilter(
        event_type=event_type,
        service_source=service_source,
        user_id=user_id,
        company_id=company_id,
        correlation_id=correlation_id,
        date_from=_parse_dt(date_from),
        date_to=_parse_dt(date_to),
        skip=skip,
        limit=limit,
    )
    return await service.query_logs(filters)


@router.get(
    "/logs/{log_id}",
    response_model=AuditLogResponse,
    summary="Get a single audit log entry",
)
async def get_audit_log(
    log_id: UUID,
    _user: dict = Depends(require_hr_or_admin),
    service: AuditService = Depends(get_audit_service),
):
    log = await service.get_log(log_id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found")
    return log


@router.get(
    "/logs/export/csv",
    summary="Export audit logs as CSV",
    description="Super Admin only. Rate-limited to 5 requests per minute.",
)
@limiter.limit("5/minute")
async def export_audit_logs_csv(
    request: Request,
    event_type: Optional[str] = Query(None),
    service_source: Optional[str] = Query(None),
    user_id: Optional[UUID] = Query(None),
    company_id: Optional[UUID] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(1000, ge=1, le=10000),
    _user: dict = Depends(require_super_admin),
    service: AuditService = Depends(get_audit_service),
):
    from datetime import datetime

    def _parse_dt(s):
        try:
            return datetime.fromisoformat(s) if s else None
        except ValueError:
            return None

    # super_admin can query any company; all others are scoped to their own company
    effective_company_id = company_id
    if _user.get("role") != "super_admin":
        jwt_company_id = _user.get("company_id")
        if not jwt_company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No company context in token")
        effective_company_id = UUID(jwt_company_id)

    filters = AuditLogFilter(
        event_type=event_type,
        service_source=service_source,
        user_id=user_id,
        company_id=effective_company_id,
        date_from=_parse_dt(date_from),
        date_to=_parse_dt(date_to),
        skip=0,
        limit=limit,
    )
    result = await service.query_logs(filters)

    # Build ORM objects from response for CSV serialization
    from app.models.audit_log import AuditLog
    mock_logs = [
        type("_", (), {col: getattr(item, col, None) for col in [
            "id","event_id","event_version","event_type","service_source",
            "company_id","user_id","correlation_id","ip_address","user_agent",
            "http_method","endpoint","timestamp","created_at"
        ]})()
        for item in result.items
    ]
    csv_content = audit_logs_to_csv(mock_logs)

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
    )
