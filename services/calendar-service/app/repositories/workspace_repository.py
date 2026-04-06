from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember


async def get_workspace(db: AsyncSession, workspace_id: UUID, company_id: str) -> Optional[Workspace]:
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.company_id == company_id,
            Workspace.is_deleted == False,
        )
    )
    return result.scalars().first()


async def list_workspaces_for_employee(db: AsyncSession, company_id: str, employee_id: UUID) -> List[Workspace]:
    """Return workspaces the employee owns or is a member of."""
    owned_result = await db.execute(
        select(Workspace).where(
            Workspace.company_id == company_id,
            Workspace.owner_id == employee_id,
            Workspace.is_deleted == False,
        )
    )
    owned_ids = {w.id for w in owned_result.scalars().all()}

    member_result = await db.execute(
        select(WorkspaceMember.workspace_id).where(
            WorkspaceMember.company_id == company_id,
            WorkspaceMember.employee_id == employee_id,
            WorkspaceMember.is_deleted == False,
        )
    )
    member_workspace_ids = {row[0] for row in member_result.all()}
    all_ids = owned_ids | member_workspace_ids

    if not all_ids:
        return []

    result = await db.execute(
        select(Workspace).where(
            Workspace.id.in_(all_ids),
            Workspace.is_deleted == False,
        )
    )
    return result.scalars().all()


async def list_members(db: AsyncSession, workspace_id: UUID, company_id: str) -> List[WorkspaceMember]:
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.company_id == company_id,
            WorkspaceMember.is_deleted == False,
        )
    )
    return result.scalars().all()


async def get_member(db: AsyncSession, workspace_id: UUID, employee_id: UUID) -> Optional[WorkspaceMember]:
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.employee_id == employee_id,
            WorkspaceMember.is_deleted == False,
        )
    )
    return result.scalars().first()
