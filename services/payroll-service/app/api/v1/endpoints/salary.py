from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from app.api.v1.dependencies import get_payroll_service, require_hr_or_admin
from app.core.security import TokenPayload
from app.schemas.payroll import (
    SalaryStructureCreate, SalaryStructureResponse,
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
    _user: TokenPayload = Depends(require_hr_or_admin()),
    service: PayrollService = Depends(get_payroll_service),
):
    return await service.list_structures()


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
