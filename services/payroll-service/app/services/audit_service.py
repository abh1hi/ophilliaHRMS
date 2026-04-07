"""Payroll audit trail service.

Records immutable audit logs for all payroll operations (state transitions, approvals, locks).
Audit logs are append-only and can never be deleted/modified.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payroll import PayrollAuditLog
from app.core.constants import AuditAction, AuditEntityType

logger = logging.getLogger(__name__)


class AuditService:
    """Service for recording audit trail entries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_action(
        self,
        company_id: UUID,
        entity_type: str,
        entity_id: UUID,
        action: str,
        performed_by: UUID,
        run_id: Optional[UUID] = None,
        payslip_id: Optional[UUID] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> PayrollAuditLog:
        """Record an audit log entry.

        Args:
            company_id: Company UUID
            entity_type: Entity type (e.g., "PAYROLL_RUN", "PAYSLIP")
            entity_id: Entity UUID
            action: Action performed (e.g., "CREATED", "APPROVED")
            performed_by: User ID who performed action
            run_id: PayrollRun ID (optional, for run-related actions)
            payslip_id: Payslip ID (optional, for payslip-related actions)
            before_state: State before action (optional snapshot)
            after_state: State after action (optional snapshot)
            ip_address: Client IP address (optional)
            user_agent: Client user agent (optional)

        Returns:
            Created PayrollAuditLog record
        """
        log = PayrollAuditLog(
            company_id=company_id,
            run_id=run_id,
            payslip_id=payslip_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            performed_by=performed_by,
            performed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(log)
        await self.db.flush()

        logger.info(
            f"Audit: {entity_type} {entity_id} — {action}",
            extra={
                "audit_entity_type": entity_type,
                "audit_action": action,
                "audit_performed_by": str(performed_by),
            },
        )

        return log

    async def log_payroll_run_created(
        self,
        company_id: UUID,
        run_id: UUID,
        created_by: UUID,
        run_data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> PayrollAuditLog:
        """Log payroll run creation."""
        return await self.log_action(
            company_id=company_id,
            entity_type=AuditEntityType.PAYROLL_RUN.value,
            entity_id=run_id,
            action=AuditAction.CREATED.value,
            performed_by=created_by,
            run_id=run_id,
            after_state=run_data,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_payroll_run_computed(
        self,
        company_id: UUID,
        run_id: UUID,
        computed_by: UUID,
        before_state: Dict[str, Any],
        after_state: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> PayrollAuditLog:
        """Log payroll computation (DRAFT → REVIEW)."""
        return await self.log_action(
            company_id=company_id,
            entity_type=AuditEntityType.PAYROLL_RUN.value,
            entity_id=run_id,
            action=AuditAction.COMPUTED.value,
            performed_by=computed_by,
            run_id=run_id,
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_payroll_run_approved(
        self,
        company_id: UUID,
        run_id: UUID,
        approved_by: UUID,
        before_state: Dict[str, Any],
        after_state: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> PayrollAuditLog:
        """Log payroll approval (REVIEW → APPROVED)."""
        return await self.log_action(
            company_id=company_id,
            entity_type=AuditEntityType.PAYROLL_RUN.value,
            entity_id=run_id,
            action=AuditAction.APPROVED.value,
            performed_by=approved_by,
            run_id=run_id,
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_payroll_run_rejected(
        self,
        company_id: UUID,
        run_id: UUID,
        rejected_by: UUID,
        before_state: Dict[str, Any],
        after_state: Dict[str, Any],
        rejection_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> PayrollAuditLog:
        """Log payroll rejection (REVIEW → DRAFT)."""
        if rejection_reason:
            after_state["rejection_reason"] = rejection_reason

        return await self.log_action(
            company_id=company_id,
            entity_type=AuditEntityType.PAYROLL_RUN.value,
            entity_id=run_id,
            action=AuditAction.REJECTED.value,
            performed_by=rejected_by,
            run_id=run_id,
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_payroll_run_processing_started(
        self,
        company_id: UUID,
        run_id: UUID,
        processed_by: UUID,
        before_state: Dict[str, Any],
        after_state: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> PayrollAuditLog:
        """Log payroll processing start (APPROVED → PROCESSING)."""
        return await self.log_action(
            company_id=company_id,
            entity_type=AuditEntityType.PAYROLL_RUN.value,
            entity_id=run_id,
            action=AuditAction.PROCESSING_STARTED.value,
            performed_by=processed_by,
            run_id=run_id,
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_payroll_run_locked(
        self,
        company_id: UUID,
        run_id: UUID,
        locked_by: UUID,
        before_state: Dict[str, Any],
        after_state: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> PayrollAuditLog:
        """Log payroll lock (PAID → LOCKED)."""
        return await self.log_action(
            company_id=company_id,
            entity_type=AuditEntityType.PAYROLL_RUN.value,
            entity_id=run_id,
            action=AuditAction.LOCKED.value,
            performed_by=locked_by,
            run_id=run_id,
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_payroll_run_marked_paid(
        self,
        company_id: UUID,
        run_id: UUID,
        marked_by: UUID,
        before_state: Dict[str, Any],
        after_state: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> PayrollAuditLog:
        """Log payroll marked as paid (COMPLETED → PAID)."""
        return await self.log_action(
            company_id=company_id,
            entity_type=AuditEntityType.PAYROLL_RUN.value,
            entity_id=run_id,
            action=AuditAction.MARKED_PAID.value,
            performed_by=marked_by,
            run_id=run_id,
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
            user_agent=user_agent,
        )
