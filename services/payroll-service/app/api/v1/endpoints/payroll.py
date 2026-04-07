from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from datetime import date

from app.api.v1.dependencies import get_payroll_service, require_hr_or_admin
from app.core.security import TokenPayload, get_current_user
from app.schemas.payroll import PayrollRunCreate, PayrollRunResponse, PayslipResponse
from app.services.payroll_service import PayrollService
from app.services.fnf_service import FNFService
from app.events.publisher import publish_event
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

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


# ── Payroll Lifecycle Endpoints ───────────────────────────────────────────

@router.post("/runs/{run_id}/compute")
async def compute_payroll(
    run_id: UUID,
    dry_run: bool = False,
    user: TokenPayload = Depends(require_hr_or_admin()),
    service: PayrollService = Depends(get_payroll_service),
):
    """Compute payroll (DRAFT → REVIEW).

    Args:
        run_id: PayrollRun ID
        dry_run: If True, return preview without persisting (for HR review)

    Returns:
        Payslips preview + errors/warnings. If dry_run=False, transitions to REVIEW.
    """
    try:
        result = await service.compute_payroll(run_id, computed_by=UUID(user.sub))

        if dry_run:
            # Dry-run: return preview without state transition
            return {
                "status": "preview",
                "run_id": str(result["run"].id),
                "payslips_count": len(result["payslips_preview"]),
                "errors": result["errors"],
                "warnings": result["warnings"],
                "is_valid": result["is_valid"],
                "payslips": result["payslips_preview"],
                "note": "Dry-run: No state transition. Create a new run to process.",
            }
        else:
            # Normal: transition to REVIEW
            return {
                "status": "review",
                "run": result["run"],
                "payslips_count": len(result["payslips_preview"]),
                "errors": result["errors"],
                "warnings": result["warnings"],
                "is_valid": result["is_valid"],
                "message": f"Payroll transitioned to REVIEW. Found {len(result['errors'])} errors, {len(result['warnings'])} warnings.",
            }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/runs/{run_id}/approve")
async def approve_payroll(
    run_id: UUID,
    user: TokenPayload = Depends(require_hr_or_admin()),
    service: PayrollService = Depends(get_payroll_service),
):
    """Approve payroll (REVIEW → APPROVED)."""
    try:
        result = await service.approve_payroll(run_id, approved_by=UUID(user.sub))
        return {
            "status": result.status,
            "run_id": str(result.id),
            "message": "Payroll approved and ready for processing.",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/runs/{run_id}/reject")
async def reject_payroll(
    run_id: UUID,
    reason: str = "",
    user: TokenPayload = Depends(require_hr_or_admin()),
    service: PayrollService = Depends(get_payroll_service),
):
    """Reject payroll (REVIEW → DRAFT)."""
    try:
        result = await service.reject_payroll(
            run_id,
            rejected_by=UUID(user.sub),
            rejection_reason=reason,
        )
        return {
            "status": result.status,
            "run_id": str(result.id),
            "message": "Payroll rejected. You can re-compute and resubmit.",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/runs/{run_id}/process")
async def process_payroll(
    run_id: UUID,
    user: TokenPayload = Depends(require_hr_or_admin()),
    service: PayrollService = Depends(get_payroll_service),
):
    """Process payroll (APPROVED → COMPLETED).

    Persists payslips, locks them, updates YTD, publishes events.
    """
    try:
        result = await service.process_payroll(run_id, processed_by=UUID(user.sub))
        return {
            "status": result.status,
            "run_id": str(result.id),
            "total_employees": result.total_employees,
            "total_gross": str(result.total_gross),
            "total_net": str(result.total_net),
            "message": f"Payroll processed: {result.total_employees} employees, ₹{result.total_net} net",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/runs/{run_id}/mark-paid")
async def mark_payroll_paid(
    run_id: UUID,
    user: TokenPayload = Depends(require_hr_or_admin()),
    service: PayrollService = Depends(get_payroll_service),
):
    """Mark payroll as paid (COMPLETED → PAID)."""
    try:
        result = await service.mark_payroll_paid(run_id)
        return {
            "status": result.status,
            "run_id": str(result.id),
            "message": "Payroll marked as paid.",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/runs/{run_id}/lock")
async def lock_payroll(
    run_id: UUID,
    user: TokenPayload = Depends(require_hr_or_admin()),
    service: PayrollService = Depends(get_payroll_service),
):
    """Lock payroll (PAID → LOCKED). Terminal state; no further edits allowed."""
    try:
        result = await service.lock_payroll(run_id)
        return {
            "status": result.status,
            "run_id": str(result.id),
            "message": "Payroll locked. No further modifications allowed.",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ── Full & Final Settlement Endpoints ───────────────────────────────────

class FNFComputeRequest:
    """Request body for FNF computation."""
    employee_id: UUID
    last_working_day: date
    joining_date: date


class FNFSummaryResponse:
    """FNF summary response."""
    employee_id: UUID
    employee_name: str
    net_fnf: str
    gratuity_amount: str
    leave_encashment_amount: str
    final_tds_adjustment: str
    total_loan_recovery: str
    warnings: List[str]


@router.post("/fnf/compute")
async def compute_fnf(
    employee_id: UUID,
    last_working_day: date,
    joining_date: date,
    user: TokenPayload = Depends(require_hr_or_admin()),
    db: AsyncSession = Depends(get_db),
):
    """Compute Full & Final Settlement for an employee.

    Returns FNF summary with gratuity, leave encashment, TDS adjustment, loan recovery.
    """
    try:
        company_id = UUID(user.company_id)
        fnf_service = FNFService(db)
        summary = await fnf_service.compute_fnf(employee_id, company_id, last_working_day, joining_date)
        return {
            "employee_id": str(summary.employee_id),
            "employee_name": summary.employee_name,
            "last_working_day": summary.last_working_day.isoformat(),
            "years_of_service": str(summary.years_of_service),
            "final_salary_pro_rata": str(summary.final_salary_pro_rata),
            "gratuity": {
                "eligible": summary.gratuity.eligible,
                "gratuity_amount": str(summary.gratuity.gratuity_amount),
                "exempt_amount": str(summary.gratuity.exempt_amount),
                "taxable_amount": str(summary.gratuity.taxable_amount),
                "note": summary.gratuity.note,
            },
            "leave_encashment": {
                "earned_leave_balance": summary.leave_encashment.earned_leave_balance,
                "encashment_amount": str(summary.leave_encashment.encashment_amount),
                "exempt_amount": str(summary.leave_encashment.exempt_amount),
                "taxable_amount": str(summary.leave_encashment.taxable_amount),
                "note": summary.leave_encashment.note,
            },
            "final_tds_adjustment": str(summary.final_tds_adjustment),
            "total_loan_recovery": str(summary.total_loan_recovery),
            "gross_fnf": str(summary.gross_fnf),
            "total_deductions_fnf": str(summary.total_deductions_fnf),
            "net_fnf": str(summary.net_fnf),
            "net_fnf_negative": summary.net_fnf_negative,
            "loan_recovery_shortfall": str(summary.loan_recovery_shortfall),
            "warnings": summary.warnings,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/fnf/create-payroll")
async def create_fnf_payroll(
    employee_id: UUID,
    last_working_day: date,
    joining_date: date,
    user: TokenPayload = Depends(require_hr_or_admin()),
    db: AsyncSession = Depends(get_db),
):
    """Create and process FNF payroll run for an employee.

    Returns PayrollRun + FNFSummary. Payslip is locked immediately (terminal state).
    """
    try:
        company_id = UUID(user.company_id)
        fnf_service = FNFService(db)
        payroll_run, summary = await fnf_service.create_fnf_payroll_run(
            company_id=company_id,
            employee_id=employee_id,
            last_working_day=last_working_day,
            joining_date=joining_date,
            approved_by=UUID(user.sub),
        )

        # Publish event
        await publish_event("fnf.processed", {
            "company_id": str(company_id),
            "employee_id": str(employee_id),
            "run_id": str(payroll_run.id),
            "net_fnf": str(summary.net_fnf),
            "user_id": user.sub,
        })

        return {
            "run_id": str(payroll_run.id),
            "status": payroll_run.status,
            "net_fnf": str(summary.net_fnf),
            "gratuity": str(summary.gratuity.gratuity_amount),
            "leave_encashment": str(summary.leave_encashment.encashment_amount),
            "message": "FNF payroll processed. Payslip is locked.",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
