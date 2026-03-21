from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from app.api.v1.dependencies import get_payroll_service, require_hr_or_admin
from app.core.security import TokenPayload, get_current_user
from app.schemas.payroll import PayrollRunCreate, PayrollRunResponse, PayslipResponse
from app.services.payroll_service import PayrollService
from app.events.publisher import publish_event

router = APIRouter(prefix="/payroll", tags=["payroll"])


@router.post("/run", response_model=PayrollRunResponse, status_code=status.HTTP_201_CREATED)
async def run_payroll(
    data: PayrollRunCreate,
    user: TokenPayload = Depends(require_hr_or_admin()),
    service: PayrollService = Depends(get_payroll_service),
):
    """Execute payroll run. IDEMPOTENT — rejects duplicate runs for same period.

    Status transitions: DRAFT → PROCESSING → COMPLETED | FAILED
    All payslips are generated atomically in a single transaction.
    """
    try:
        result = await service.run_payroll(data, processed_by=UUID(user.sub))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    # Emit audit event for payroll run
    if result.status == "COMPLETED":
        await publish_event("payroll.run", {
            "company_id": str(result.company_id),
            "user_id": user.sub,
            "payroll_run_id": str(result.id),
            "period_start": result.period_start.isoformat(),
            "period_end": result.period_end.isoformat(),
            "total_employees": result.total_employees,
            "total_net": str(result.total_net),
        })

    return result


@router.get("/runs", response_model=List[PayrollRunResponse])
async def list_payroll_runs(
    skip: int = 0,
    limit: int = 100,
    _user: TokenPayload = Depends(require_hr_or_admin()),
    service: PayrollService = Depends(get_payroll_service),
):
    return await service.list_payroll_runs(skip=skip, limit=limit)


@router.get("/runs/{run_id}", response_model=PayrollRunResponse)
async def get_payroll_run(
    run_id: UUID,
    _user: TokenPayload = Depends(require_hr_or_admin()),
    service: PayrollService = Depends(get_payroll_service),
):
    result = await service.get_payroll_run(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    return result


@router.get("/runs/{run_id}/payslips", response_model=List[PayslipResponse])
async def get_payslips_by_run(
    run_id: UUID,
    _user: TokenPayload = Depends(require_hr_or_admin()),
    service: PayrollService = Depends(get_payroll_service),
):
    return await service.get_payslips(run_id)


@router.get("/my-payslips", response_model=List[PayslipResponse])
async def get_my_payslips(
    user: TokenPayload = Depends(get_current_user),
    service: PayrollService = Depends(get_payroll_service),
):
    """Employee views their own payslips."""
    return await service.get_employee_payslips(UUID(user.sub))
