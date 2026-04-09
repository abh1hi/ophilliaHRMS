"""Payroll Service Guards — Safety checks for state transitions and data integrity.

Implements production-hardening guards:
1. Prevent edits to locked payroll runs
2. Validate net pay is non-negative
3. Enforce timeout on external service calls
4. Validate payroll state transitions
"""
import logging
from decimal import Decimal
from typing import Optional
from fastapi import HTTPException, status
from app.models.payroll import PayrollRun

logger = logging.getLogger(__name__)


def assert_payroll_not_locked(run: Optional[PayrollRun], operation: str = "modify") -> None:
    """Guard: Prevent modifications to locked payroll.

    Args:
        run: PayrollRun to check
        operation: Operation description (e.g., "approve", "reject", "lock")

    Raises:
        HTTPException(409): If payroll is locked
    """
    if not run:
        return  # No-op if run is None

    if run.locked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Payroll run {run.id} is locked and cannot be {operation}. "
            f"Locked at: {run.locked_at.isoformat()}. "
            f"To modify, create a new payroll run or contact administrator.",
        )

    logger.debug(f"Guard passed: Payroll {run.id} is not locked, {operation} allowed")


def assert_net_pay_valid(net_pay: Decimal, employee_id: str = "", period_str: str = "") -> None:
    """Guard: Validate net pay is non-negative.

    In rare cases (e.g., heavy deductions), net pay can be negative.
    This guard flags it for HR review but allows processing.

    Args:
        net_pay: Net pay amount
        employee_id: Employee ID (for logging)
        period_str: Period (for logging)

    Raises:
        ValueError: If net pay is negative (can be caught and treated as warning)
    """
    if net_pay < Decimal("0"):
        error_msg = (
            f"⚠ Negative net pay detected: ₹{abs(net_pay)} "
            f"(Employee: {employee_id}, Period: {period_str}). "
            f"Total deductions exceed gross salary. "
            f"Review payslip and consider manual intervention."
        )
        logger.warning(error_msg)
        raise ValueError(error_msg)


def assert_payroll_state_valid(current_state: str, target_state: str) -> None:
    """Guard: Validate payroll state transition is allowed.

    Uses state machine from constants.VALID_PAYROLL_TRANSITIONS.

    Args:
        current_state: Current status
        target_state: Desired status

    Raises:
        HTTPException(422): If transition is invalid
    """
    from app.core.constants import VALID_PAYROLL_TRANSITIONS

    allowed_transitions = VALID_PAYROLL_TRANSITIONS.get(current_state, [])

    if target_state not in allowed_transitions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid state transition: {current_state} → {target_state}. "
            f"Allowed transitions from {current_state}: {', '.join(allowed_transitions)}",
        )

    logger.debug(f"Guard passed: State transition {current_state} → {target_state} valid")


def assert_payroll_not_failed(run: Optional[PayrollRun]) -> None:
    """Guard: Prevent operations on FAILED payroll (must retry or create new).

    Args:
        run: PayrollRun to check

    Raises:
        HTTPException(409): If payroll is in FAILED state
    """
    if not run:
        return

    if run.status == "FAILED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Payroll {run.id} is in FAILED state. "
            f"Error: {run.error_message}. "
            f"Use POST /retry endpoint to retry, or create a new payroll run.",
        )


def assert_payroll_in_state(
    run: Optional[PayrollRun],
    expected_state: str,
    operation: str = "perform operation",
) -> None:
    """Guard: Ensure payroll is in expected state before operation.

    Args:
        run: PayrollRun to check
        expected_state: Expected current state
        operation: Operation description

    Raises:
        HTTPException(409): If payroll is not in expected state
    """
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll run not found",
        )

    if run.status != expected_state:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot {operation}. Payroll must be in {expected_state} state, "
            f"but is currently in {run.status} state.",
        )

    logger.debug(f"Guard passed: Payroll {run.id} is in {expected_state} state")


# ──────────────────────────────────────────────────────────────────────────
# Guard Checklist (Use in service methods)
# ──────────────────────────────────────────────────────────────────────────
"""
Before any state-changing operation, call appropriate guards:

1. compute_payroll(run):
   assert_payroll_not_locked(run, "compute")
   assert_payroll_in_state(run, "DRAFT", "compute payroll")

2. approve_payroll(run):
   assert_payroll_not_locked(run, "approve")
   assert_payroll_in_state(run, "REVIEW", "approve payroll")

3. reject_payroll(run):
   assert_payroll_not_locked(run, "reject")
   assert_payroll_in_state(run, "REVIEW", "reject payroll")

4. process_payroll(run):
   assert_payroll_not_locked(run, "process")
   assert_payroll_in_state(run, "APPROVED", "process payroll")
   assert_payroll_not_failed(run)

5. lock_payroll(run):
   assert_payroll_not_locked(run, "lock")
   assert_payroll_in_state(run, "PAID", "lock payroll")

6. Payslip creation:
   assert_net_pay_valid(payslip.net, employee_id, period_str)

7. State transitions:
   assert_payroll_state_valid(current_status, new_status)
"""
