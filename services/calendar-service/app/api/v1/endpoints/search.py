from fastapi import APIRouter
from typing import Optional
from uuid import UUID

from app.api.v1.dependencies import DB, AnyUser
from app.core.responses import APIResponse
from app.services.search_service import search

router = APIRouter()


@router.get("/", response_model=APIResponse[dict])
async def search_calendar(
    q: str,
    type: Optional[str] = None,    # "events" | "tasks" | "comments"
    workspace_id: Optional[UUID] = None,
    fields: Optional[str] = None,  # sparse: "id,title,start_time"
    limit: int = 20,
    *,
    db: DB,
    current_user: AnyUser,
):
    results = await search(db, current_user.company_id, q, type, workspace_id, fields, limit)
    return APIResponse(success=True, data=results)
