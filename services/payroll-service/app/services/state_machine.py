"""Payroll state machine — validates and enforces transitions.

Implements the strict state transition rules:
DRAFT → REVIEW → APPROVED → PROCESSING → COMPLETED → PAID → LOCKED
With rejection path: REVIEW → DRAFT
And retry path: FAILED → DRAFT
"""
from typing import List

from app.core.constants import PayrollStatus, VALID_PAYROLL_TRANSITIONS


class InvalidTransitionError(Exception):
    """Raised when state transition is not allowed."""

    pass


class StateMachine:
    """Payroll state machine validator."""

    @staticmethod
    def validate_transition(current_status: str, target_status: str) -> None:
        """Validate that transition is allowed.

        Args:
            current_status: Current PayrollStatus value (e.g., "DRAFT")
            target_status: Target PayrollStatus value (e.g., "REVIEW")

        Raises:
            InvalidTransitionError if transition not allowed
        """
        try:
            current = PayrollStatus(current_status)
        except ValueError:
            raise InvalidTransitionError(f"Unknown current status: {current_status}")

        try:
            target = PayrollStatus(target_status)
        except ValueError:
            raise InvalidTransitionError(f"Unknown target status: {target_status}")

        allowed_targets = VALID_PAYROLL_TRANSITIONS.get(current, [])

        if target not in allowed_targets:
            raise InvalidTransitionError(
                f"Cannot transition {current.value} → {target.value}. "
                f"Allowed: {[s.value for s in allowed_targets]}"
            )

    @staticmethod
    def get_allowed_transitions(current_status: str) -> List[str]:
        """Get list of allowed target statuses from current status.

        Args:
            current_status: Current PayrollStatus value

        Returns:
            List of allowed target status values
        """
        try:
            current = PayrollStatus(current_status)
        except ValueError:
            return []

        allowed = VALID_PAYROLL_TRANSITIONS.get(current, [])
        return [s.value for s in allowed]

    @staticmethod
    def is_terminal_state(status: str) -> bool:
        """Check if status is terminal (no further transitions).

        Args:
            status: PayrollStatus value

        Returns:
            True if terminal (LOCKED), False otherwise
        """
        return status == PayrollStatus.LOCKED.value

    @staticmethod
    def is_failed_state(status: str) -> bool:
        """Check if status is failed.

        Args:
            status: PayrollStatus value

        Returns:
            True if FAILED, False otherwise
        """
        return status == PayrollStatus.FAILED.value


# ──────────────────────────────────────────────────────────────────────
# COMMON VALIDATION HELPERS
# ──────────────────────────────────────────────────────────────────────

def assert_can_compute(current_status: str) -> None:
    """Assert that payroll can be computed from current status.

    Can only compute from DRAFT.
    """
    if current_status != PayrollStatus.DRAFT.value:
        raise InvalidTransitionError(
            f"Can only compute from DRAFT, current status: {current_status}"
        )


def assert_can_approve(current_status: str) -> None:
    """Assert that payroll can be approved from current status.

    Can only approve from REVIEW.
    """
    if current_status != PayrollStatus.REVIEW.value:
        raise InvalidTransitionError(
            f"Can only approve from REVIEW, current status: {current_status}"
        )


def assert_can_reject(current_status: str) -> None:
    """Assert that payroll can be rejected from current status.

    Can only reject from REVIEW.
    """
    if current_status != PayrollStatus.REVIEW.value:
        raise InvalidTransitionError(
            f"Can only reject from REVIEW, current status: {current_status}"
        )


def assert_can_process(current_status: str) -> None:
    """Assert that payroll can be processed from current status.

    Can only process from APPROVED.
    """
    if current_status != PayrollStatus.APPROVED.value:
        raise InvalidTransitionError(
            f"Can only process from APPROVED, current status: {current_status}"
        )


def assert_can_mark_paid(current_status: str) -> None:
    """Assert that payroll can be marked paid from current status.

    Can only mark paid from COMPLETED.
    """
    if current_status != PayrollStatus.COMPLETED.value:
        raise InvalidTransitionError(
            f"Can only mark paid from COMPLETED, current status: {current_status}"
        )


def assert_can_lock(current_status: str) -> None:
    """Assert that payroll can be locked from current status.

    Can only lock from PAID.
    """
    if current_status != PayrollStatus.PAID.value:
        raise InvalidTransitionError(
            f"Can only lock from PAID, current status: {current_status}"
        )


def assert_can_retry(current_status: str) -> None:
    """Assert that payroll can be retried from current status.

    Can only retry from FAILED.
    """
    if current_status != PayrollStatus.FAILED.value:
        raise InvalidTransitionError(
            f"Can only retry from FAILED, current status: {current_status}"
        )
