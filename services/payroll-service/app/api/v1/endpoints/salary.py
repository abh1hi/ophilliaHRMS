from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List
from uuid import UUID

from app.api.v1.dependencies import get_payroll_service, require_hr_or_admin
from app.core.security import TokenPayload
from app.schemas.payroll import (
    SalaryStructureCreate, SalaryStructureUpdate, SalaryStructureResponse,
    EmployeeSalaryCreate, EmployeeSalaryResponse,
)
from app.services.payroll_service import PayrollService

router = APIRouter(prefix="/salary", tags=["salary"])


@router.post("/structures", response_model=SalaryStructureResponse, status_code=status.HTTP_201_CREATED)
async def create_salary_structure(
    data: SalaryStructureCreate,
    _user: TokenPayload = Depends(require_hr_or_admin()),
    service: PayrollService = Depends(get_payroll_service),
):
    return await service.create_structure(data)


@router.get("/structures", response_model=List[SalaryStructureResponse])
async def list_salary_structures(
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = Query(False, description="Include soft-deleted structures"),
    _user: TokenPayload = Depends(require_hr_or_admin()),
    service: PayrollService = Depends(get_payroll_service),
):
    return await service.list_structures(skip=skip, limit=limit, include_inactive=include_inactive)


@router.get("/structures/{structure_id}", response_model=SalaryStructureResponse)
async def get_salary_structure(
    structure_id: UUID,
    _user: TokenPayload = Depends(require_hr_or_admin()),
    service: PayrollService = Depends(get_payroll_service),
):
    result = await service.get_structure(structure_id)
    if not result:
        raise HTTPException(status_code=404, detail="Salary structure not found")
    return result


@router.patch("/structures/{structure_id}", response_model=SalaryStructureResponse)
async def update_salary_structure(
    structure_id: UUID,
    data: SalaryStructureUpdate,
    _user: TokenPayload = Depends(require_hr_or_admin()),
    service: PayrollService = Depends(get_payroll_service),
):
    """Update salary structure percentages. HR or Super Admin only."""
    result = await service.update_structure(structure_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Salary structure not found")
    return result


@router.delete("/structures/{structure_id}", response_model=SalaryStructureResponse)
async def delete_salary_structure(
    structure_id: UUID,
    _user: TokenPayload = Depends(require_hr_or_admin()),
    service: PayrollService = Depends(get_payroll_service),
):
    """Soft delete a salary structure (sets is_active = false). HR or Super Admin only."""
    result = await service.soft_delete_structure(structure_id)
    if not result:
        raise HTTPException(status_code=404, detail="Salary structure not found")
    return result


@router.post("/assign", response_model=EmployeeSalaryResponse, status_code=status.HTTP_201_CREATED)
async def assign_employee_salary(
    data: EmployeeSalaryCreate,
    _user: TokenPayload = Depends(require_hr_or_admin()),
    service: PayrollService = Depends(get_payroll_service),
):
    """Assign salary to employee. Deactivates any previous active salary."""
    return await service.assign_salary(data)


@router.get("/employee/{employee_id}", response_model=EmployeeSalaryResponse)
async def get_employee_salary(
    employee_id: UUID,
    _user: TokenPayload = Depends(require_hr_or_admin()),
    service: PayrollService = Depends(get_payroll_service),
):
    result = await service.get_employee_salary(employee_id)
    if not result:
        raise HTTPException(status_code=404, detail="No active salary found for employee")
    return result


@router.get("/employee/{employee_id}/history", response_model=List[EmployeeSalaryResponse])
async def get_employee_salary_history(
    employee_id: UUID,
    _user: TokenPayload = Depends(require_hr_or_admin()),
    service: PayrollService = Depends(get_payroll_service),
):
    """Return all salary records for an employee (active and inactive)."""
    return await service.get_employee_salary_history(employee_id)
