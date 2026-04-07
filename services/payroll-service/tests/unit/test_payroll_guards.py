"""Unit Tests for Phase 9A Production Guards.

Tests:
- Locked payroll prevention
- Negative net pay validation
- State transition validation
- FAILED payroll handling
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from decimal import Decimal
from fastapi import HTTPException

from app.core.payroll_guards import (
    assert_payroll_not_locked,
    assert_net_pay_valid,
    assert_payroll_state_valid,
    assert_payroll_not_failed,
    assert_payroll_in_state,
)
from app.models.payroll import PayrollRun
from app.core.constants import PayrollStatus


# ──────────────────────────────────────────────────────────────────────────
# Test: Locked Payroll Prevention
# ──────────────────────────────────────────────────────────────────────────

@pytest.mark.guard
class TestLockedPayrollGuard:
    """Tests assert_payroll_not_locked()."""

    def test_unlocked_payroll_passes(self):
        """Unlocked payroll should pass guard."""
        run = PayrollRun(
            company_id=uuid4(),
            period_start=__import__("datetime").date(2026, 4, 1),
            period_end=__import__("datetime").date(2026, 4, 30),
            status=PayrollStatus.DRAFT.value,
            locked_at=None,  # Not locked
        )

        # Should not raise
        assert_payroll_not_locked(run, "approve")

    def test_locked_payroll_raises_409(self):
        """Locked payroll should raise HTTP 409."""
        run = PayrollRun(
            company_id=uuid4(),
            period_start=__import__("datetime").date(2026, 4, 1),
            period_end=__import__("datetime").date(2026, 4, 30),
            status=PayrollStatus.LOCKED.value,
            locked_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )

        with pytest.raises(HTTPException) as exc_info:
            assert_payroll_not_locked(run, "approve")

        assert exc_info.value.status_code == 409
        assert "locked" in exc_info.value.detail.lower()

    def test_none_payroll_no_op(self):
        """None payroll should be no-op (not checked)."""
        # Should not raise
        assert_payroll_not_locked(None, "approve")


# ──────────────────────────────────────────────────────────────────────────
# Test: Negative Net Pay Validation
# ──────────────────────────────────────────────────────────────────────────

@pytest.mark.guard
class TestNegativeNetPayGuard:
    """Tests assert_net_pay_valid()."""

    def test_positive_net_pay_passes(self):
        """Positive net pay should pass."""
        assert_net_pay_valid(
            net_pay=Decimal("85000.00"),
            employee_id="emp-001",
            period_str="2026-04-01 to 2026-04-30",
        )

    def test_zero_net_pay_passes(self):
        """Zero net pay is valid (edge case)."""
        assert_net_pay_valid(
            net_pay=Decimal("0.00"),
            employee_id="emp-001",
            period_str="2026-04-01 to 2026-04-30",
        )

    def test_negative_net_pay_raises(self):
        """Negative net pay should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            assert_net_pay_valid(
                net_pay=Decimal("-5000.00"),
                employee_id="emp-001",
                period_str="2026-04-01 to 2026-04-30",
            )

        assert "negative" in str(exc_info.value).lower()


# ──────────────────────────────────────────────────────────────────────────
# Test: State Transition Validation
# ──────────────────────────────────────────────────────────────────────────

@pytest.mark.guard
class TestStateTransitionGuard:
    """Tests assert_payroll_state_valid()."""

    def test_valid_draft_to_review(self):
        """DRAFT → REVIEW should be valid."""
        assert_payroll_state_valid("DRAFT", "REVIEW")

    def test_valid_review_to_approved(self):
        """REVIEW → APPROVED should be valid."""
        assert_payroll_state_valid("REVIEW", "APPROVED")

    def test_valid_approved_to_processing(self):
        """APPROVED → PROCESSING should be valid."""
        assert_payroll_state_valid("APPROVED", "PROCESSING")

    def test_valid_review_to_draft_reject(self):
        """REVIEW → DRAFT (reject) should be valid."""
        assert_payroll_state_valid("REVIEW", "DRAFT")

    def test_invalid_draft_to_approved_skip_review(self):
        """DRAFT → APPROVED (skipping REVIEW) should be invalid."""
        with pytest.raises(HTTPException) as exc_info:
            assert_payroll_state_valid("DRAFT", "APPROVED")

        assert exc_info.value.status_code == 422

    def test_invalid_completed_to_draft(self):
        """COMPLETED → DRAFT should be invalid (no going back)."""
        with pytest.raises(HTTPException) as exc_info:
            assert_payroll_state_valid("COMPLETED", "DRAFT")

        assert exc_info.value.status_code == 422

    def test_invalid_locked_to_paid(self):
        """LOCKED → PAID should be invalid (no backward transition)."""
        with pytest.raises(HTTPException) as exc_info:
            assert_payroll_state_valid("LOCKED", "PAID")

        assert exc_info.value.status_code == 422


# ──────────────────────────────────────────────────────────────────────────
# Test: FAILED Payroll Guard
# ──────────────────────────────────────────────────────────────────────────

@pytest.mark.guard
class TestFailedPayrollGuard:
    """Tests assert_payroll_not_failed()."""

    def test_non_failed_payroll_passes(self):
        """Non-FAILED payroll should pass."""
        run = PayrollRun(
            company_id=uuid4(),
            period_start=__import__("datetime").date(2026, 4, 1),
            period_end=__import__("datetime").date(2026, 4, 30),
            status=PayrollStatus.DRAFT.value,
            error_message=None,
        )

        assert_payroll_not_failed(run)

    def test_failed_payroll_raises_409(self):
        """FAILED payroll should raise HTTP 409."""
        run = PayrollRun(
            company_id=uuid4(),
            period_start=__import__("datetime").date(2026, 4, 1),
            period_end=__import__("datetime").date(2026, 4, 30),
            status=PayrollStatus.FAILED.value,
            error_message="Employee emp-001 has no salary structure",
        )

        with pytest.raises(HTTPException) as exc_info:
            assert_payroll_not_failed(run)

        assert exc_info.value.status_code == 409
        assert "failed" in exc_info.value.detail.lower()

    def test_none_payroll_no_op(self):
        """None payroll should be no-op."""
        assert_payroll_not_failed(None)


# ──────────────────────────────────────────────────────────────────────────
# Test: Payroll State Requirement Guard
# ──────────────────────────────────────────────────────────────────────────

@pytest.mark.guard
class TestPayrollStateRequirementGuard:
    """Tests assert_payroll_in_state()."""

    def test_payroll_in_expected_state(self):
        """Payroll in expected state should pass."""
        run = PayrollRun(
            company_id=uuid4(),
            period_start=__import__("datetime").date(2026, 4, 1),
            period_end=__import__("datetime").date(2026, 4, 30),
            status=PayrollStatus.REVIEW.value,
        )

        assert_payroll_in_state(run, "REVIEW", "approve payroll")

    def test_payroll_not_in_expected_state(self):
        """Payroll not in expected state should raise 409."""
        run = PayrollRun(
            company_id=uuid4(),
            period_start=__import__("datetime").date(2026, 4, 1),
            period_end=__import__("datetime").date(2026, 4, 30),
            status=PayrollStatus.DRAFT.value,
        )

        with pytest.raises(HTTPException) as exc_info:
            assert_payroll_in_state(run, "REVIEW", "approve payroll")

        assert exc_info.value.status_code == 409
        assert "must be in REVIEW" in exc_info.value.detail

    def test_none_payroll_raises_404(self):
        """None payroll should raise 404."""
        with pytest.raises(HTTPException) as exc_info:
            assert_payroll_in_state(None, "DRAFT", "process")

        assert exc_info.value.status_code == 404


# ──────────────────────────────────────────────────────────────────────────
# Integration: Guard Chain
# ──────────────────────────────────────────────────────────────────────────

@pytest.mark.guard
class TestGuardChain:
    """Tests multiple guards in sequence (typical workflow)."""

    def test_compute_guard_chain(self):
        """Compute should check: not locked, in DRAFT state."""
        run = PayrollRun(
            company_id=uuid4(),
            period_start=__import__("datetime").date(2026, 4, 1),
            period_end=__import__("datetime").date(2026, 4, 30),
            status=PayrollStatus.DRAFT.value,
            locked_at=None,
        )

        # All guards should pass
        assert_payroll_not_locked(run, "compute")
        assert_payroll_state_valid(run.status, "REVIEW")
        # No failure or FAILED check needed for compute

    def test_approve_guard_chain(self):
        """Approve should check: not locked, in REVIEW state."""
        run = PayrollRun(
            company_id=uuid4(),
            period_start=__import__("datetime").date(2026, 4, 1),
            period_end=__import__("datetime").date(2026, 4, 30),
            status=PayrollStatus.REVIEW.value,
            locked_at=None,
        )

        # All guards should pass
        assert_payroll_not_locked(run, "approve")
        assert_payroll_state_valid(run.status, "APPROVED")

    def test_process_guard_chain_blocks_failed(self):
        """Process should block FAILED payroll."""
        run = PayrollRun(
            company_id=uuid4(),
            period_start=__import__("datetime").date(2026, 4, 1),
            period_end=__import__("datetime").date(2026, 4, 30),
            status=PayrollStatus.FAILED.value,
            error_message="Test error",
        )

        # Should block on FAILED check
        with pytest.raises(HTTPException):
            assert_payroll_not_failed(run)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "guard"])
