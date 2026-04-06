from fastapi import APIRouter
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.api.v1.dependencies import DB, HRAdminUser
from app.schemas.audit_log import AuditLogResponse
from app.core.responses import APIResponse
from app.repositories.audit_repository import list_audit_logs

router = APIRouter()


@router.get("/", response_model=APIResponse[List[AuditLogResponse]])
async def get_audit_logs(
    resource_type: Optional[str] = None,
    resource_id: Optional[UUID] = None,
    actor_id: Optional[UUID] = None,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 50,
    *,
    db: DB,
    current_user: HRAdminUser,
):
    logs = await list_audit_logs(
        db, current_user.company_id,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_id=actor_id,
        from_dt=from_dt,
        to_dt=to_dt,
        skip=skip,
        limit=limit,
    )
    return APIResponse(success=True, data=logs)
