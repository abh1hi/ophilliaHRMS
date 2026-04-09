from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.core.responses import ok
from app.services.branch_service import BranchService
from app.schemas.branch import BranchCreate, BranchUpdate, BranchResponse

router = APIRouter(prefix="/branches", tags=["branches"])


def _get_service(db: AsyncSession = Depends(get_db_with_tenant)) -> BranchService:
    return BranchService(db)


@router.get("")
async def list_branches(
    include_inactive: bool = Query(False),
    _: TokenPayload = Depends(get_current_user),
    service: BranchService = Depends(_get_service),
):
    items, _ = await service.list_all(include_inactive=include_inactive)
    return ok([BranchResponse.model_validate(x).model_dump(mode="json") for x in items])


@router.get("/{branch_id}")
async def get_branch(
    branch_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    service: BranchService = Depends(_get_service),
):
    return ok(BranchResponse.model_validate(await service.get(branch_id)).model_dump(mode="json"))


@router.post("", status_code=201)
async def create_branch(
    data: BranchCreate,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: BranchService = Depends(_get_service),
):
    return ok(BranchResponse.model_validate(await service.create(data)).model_dump(mode="json"))


@router.patch("/{branch_id}")
async def update_branch(
    branch_id: UUID,
    data: BranchUpdate,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: BranchService = Depends(_get_service),
):
    return ok(BranchResponse.model_validate(await service.update(branch_id, data)).model_dump(mode="json"))


@router.delete("/{branch_id}")
async def delete_branch(
    branch_id: UUID,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: BranchService = Depends(_get_service),
):
    return ok(BranchResponse.model_validate(await service.soft_delete(branch_id)).model_dump(mode="json"))
