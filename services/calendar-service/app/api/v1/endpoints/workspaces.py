from fastapi import APIRouter, status
from typing import Annotated, List
from uuid import UUID

from app.api.v1.dependencies import DB, AnyUser
from app.schemas.workspace import (
    WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse,
    WorkspaceMemberCreate, WorkspaceMemberUpdate, WorkspaceMemberResponse,
)
from app.core.responses import APIResponse
from app.repositories import workspace_repository as repo
from app.services import workspace_service as svc

router = APIRouter()


@router.get("/", response_model=APIResponse[List[WorkspaceResponse]])
async def list_workspaces(*, db: DB, current_user: AnyUser):
    from uuid import UUID
    items = await repo.list_workspaces_for_employee(db, current_user.company_id, UUID(current_user.sub))
    return APIResponse(success=True, data=items)


@router.post("/", response_model=APIResponse[WorkspaceResponse], status_code=status.HTTP_201_CREATED)
async def create_workspace(data: WorkspaceCreate, *, db: DB, current_user: AnyUser):
    ws = await svc.create_workspace(db, data, UUID(current_user.sub), current_user.company_id)
    return APIResponse(success=True, data=ws)


@router.get("/{workspace_id}", response_model=APIResponse[WorkspaceResponse])
async def get_workspace(workspace_id: UUID, *, db: DB, current_user: AnyUser):
    ws = await repo.get_workspace(db, workspace_id, current_user.company_id)
    if not ws:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Workspace not found")
    return APIResponse(success=True, data=ws)


@router.patch("/{workspace_id}", response_model=APIResponse[WorkspaceResponse])
async def update_workspace(workspace_id: UUID, data: WorkspaceUpdate, *, db: DB, current_user: AnyUser):
    ws = await svc.update_workspace(db, workspace_id, data, UUID(current_user.sub), current_user.role, current_user.company_id)
    return APIResponse(success=True, data=ws)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(workspace_id: UUID, *, db: DB, current_user: AnyUser):
    await svc.delete_workspace(db, workspace_id, UUID(current_user.sub), current_user.role, current_user.company_id)


@router.get("/{workspace_id}/members", response_model=APIResponse[List[WorkspaceMemberResponse]])
async def list_members(workspace_id: UUID, *, db: DB, current_user: AnyUser):
    members = await repo.list_members(db, workspace_id, current_user.company_id)
    return APIResponse(success=True, data=members)


@router.post("/{workspace_id}/members", response_model=APIResponse[WorkspaceMemberResponse], status_code=status.HTTP_201_CREATED)
async def add_member(workspace_id: UUID, data: WorkspaceMemberCreate, *, db: DB, current_user: AnyUser):
    member = await svc.add_member(db, workspace_id, data, UUID(current_user.sub), current_user.role, current_user.company_id)
    return APIResponse(success=True, data=member)


@router.patch("/{workspace_id}/members/{employee_id}", response_model=APIResponse[WorkspaceMemberResponse])
async def update_member(workspace_id: UUID, employee_id: UUID, data: WorkspaceMemberUpdate, *, db: DB, current_user: AnyUser):
    member = await svc.update_member_role(db, workspace_id, employee_id, data, UUID(current_user.sub), current_user.role, current_user.company_id)
    return APIResponse(success=True, data=member)


@router.delete("/{workspace_id}/members/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(workspace_id: UUID, employee_id: UUID, *, db: DB, current_user: AnyUser):
    await svc.remove_member(db, workspace_id, employee_id, UUID(current_user.sub), current_user.role, current_user.company_id)
