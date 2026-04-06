from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate, WorkspaceMemberCreate, WorkspaceMemberUpdate
from app.repositories import workspace_repository as repo
from app.core.permissions import check_permission
from app.core.cache import cache_invalidate, workspace_key


async def create_workspace(db: AsyncSession, data: WorkspaceCreate, owner_id: UUID, company_id: str) -> Workspace:
    ws = Workspace(
        **data.model_dump(),
        owner_id=owner_id,
        company_id=company_id,
    )
    db.add(ws)
    # Add owner as member with role "owner"
    member = WorkspaceMember(
        workspace_id=ws.id,
        employee_id=owner_id,
        company_id=company_id,
        role="owner",
        joined_at=datetime.now(timezone.utc),
    )
    db.add(member)
    await db.commit()
    await db.refresh(ws)
    return ws


async def update_workspace(
    db: AsyncSession, workspace_id: UUID, data: WorkspaceUpdate,
    current_user_id: UUID, current_user_role: str, company_id: str
) -> Workspace:
    ws = await repo.get_workspace(db, workspace_id, company_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    check_permission("workspace:write", current_user_role, current_user_id, ws.owner_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ws, field, value)
    await db.commit()
    await cache_invalidate(workspace_key(company_id, str(workspace_id)))
    return ws


async def delete_workspace(
    db: AsyncSession, workspace_id: UUID,
    current_user_id: UUID, current_user_role: str, company_id: str
) -> None:
    ws = await repo.get_workspace(db, workspace_id, company_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    check_permission("workspace:delete", current_user_role, current_user_id, ws.owner_id)
    ws.is_deleted = True
    ws.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    await cache_invalidate(workspace_key(company_id, str(workspace_id)))


async def add_member(
    db: AsyncSession, workspace_id: UUID, data: WorkspaceMemberCreate,
    current_user_id: UUID, current_user_role: str, company_id: str
) -> WorkspaceMember:
    ws = await repo.get_workspace(db, workspace_id, company_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    check_permission("member:manage", current_user_role, current_user_id, ws.owner_id)

    existing = await repo.get_member(db, workspace_id, data.employee_id)
    if existing:
        raise HTTPException(status_code=409, detail="Employee is already a member")

    member = WorkspaceMember(
        workspace_id=workspace_id,
        employee_id=data.employee_id,
        company_id=company_id,
        role=data.role,
        joined_at=datetime.now(timezone.utc),
        invited_by=current_user_id,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


async def update_member_role(
    db: AsyncSession, workspace_id: UUID, employee_id: UUID, data: WorkspaceMemberUpdate,
    current_user_id: UUID, current_user_role: str, company_id: str
) -> WorkspaceMember:
    ws = await repo.get_workspace(db, workspace_id, company_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    check_permission("member:manage", current_user_role, current_user_id, ws.owner_id)

    member = await repo.get_member(db, workspace_id, employee_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.role = data.role
    await db.commit()
    return member


async def remove_member(
    db: AsyncSession, workspace_id: UUID, employee_id: UUID,
    current_user_id: UUID, current_user_role: str, company_id: str
) -> None:
    ws = await repo.get_workspace(db, workspace_id, company_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    check_permission("member:manage", current_user_role, current_user_id, ws.owner_id)

    member = await repo.get_member(db, workspace_id, employee_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.is_deleted = True
    member.deleted_at = datetime.now(timezone.utc)
    await db.commit()
