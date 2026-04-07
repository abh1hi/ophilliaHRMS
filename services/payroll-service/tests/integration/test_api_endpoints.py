"""Integration Tests for Payroll API Endpoints.

Tests HTTP endpoints for payroll lifecycle:
- POST /payroll/runs (create payroll run)
- POST /payroll/runs/{id}/compute (DRAFT → REVIEW)
- POST /payroll/runs/{id}/approve (REVIEW → APPROVED)
- POST /payroll/runs/{id}/reject (REVIEW → DRAFT)
- POST /payroll/runs/{id}/process (APPROVED → COMPLETED)
- POST /payroll/runs/{id}/mark-paid (COMPLETED → PAID)
- POST /payroll/runs/{id}/lock (PAID → LOCKED)

Additional endpoints:
- GET /payroll/runs/{id}/preview (read draft payslips)
- POST /payroll/runs/{id}/retry (FAILED → DRAFT)
- GET /payroll/runs/{id}/ecr-file (export ECR)
"""
import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4
from fastapi import HTTPException
from httpx import AsyncClient

from app.core.constants import PayrollStatus


@pytest.mark.integration
class TestPayrollRunCreation:
    """Tests POST /payroll/runs endpoint."""

    @pytest.mark.asyncio
    async def test_create_payroll_run_success(self, db_session, client: AsyncClient, monkeypatch):
        """POST /payroll/runs creates run in DRAFT state."""
        company_id = uuid4()
        user_id = uuid4()

        # Mock tenant middleware
        monkeypatch.setenv("X-Company-ID", str(company_id))

        payload = {
            "period_start": date(2026, 4, 1).isoformat(),
            "period_end": date(2026, 4, 30).isoformat(),
            "run_type": "REGULAR",
            "idempotency_key": str(uuid4())
        }

        response = await client.post(
            "/api/v1/payroll/runs",
            json=payload,
            headers={"X-Company-ID": str(company_id), "Authorization": f"Bearer {user_id}"}
        )

        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        data = response.json()
        assert data["status"] == "DRAFT"
        assert data["period_start"] == "2026-04-01"
        assert data["period_end"] == "2026-04-30"

    @pytest.mark.asyncio
    async def test_create_payroll_run_duplicate_period_fails(self, db_session, client: AsyncClient, payroll_run, monkeypatch):
        """POST /payroll/runs with duplicate period returns 409."""
        company_id = payroll_run.company_id
        user_id = uuid4()

        monkeypatch.setenv("X-Company-ID", str(company_id))

        payload = {
            "period_start": payroll_run.period_start.isoformat(),
            "period_end": payroll_run.period_end.isoformat(),
            "run_type": "REGULAR",
            "idempotency_key": str(uuid4())
        }

        response = await client.post(
            "/api/v1/payroll/runs",
            json=payload,
            headers={"X-Company-ID": str(company_id), "Authorization": f"Bearer {user_id}"}
        )

        assert response.status_code == 409, "Duplicate period should return 409 Conflict"


@pytest.mark.integration
class TestPayrollComputeEndpoint:
    """Tests POST /payroll/runs/{id}/compute endpoint."""

    @pytest.mark.asyncio
    async def test_compute_draft_payroll_transitions_to_review(self, db_session, client: AsyncClient, payroll_run, monkeypatch):
        """POST /compute moves DRAFT → REVIEW."""
        company_id = payroll_run.company_id
        run_id = payroll_run.id
        user_id = uuid4()

        monkeypatch.setenv("X-Company-ID", str(company_id))

        response = await client.post(
            f"/api/v1/payroll/runs/{run_id}/compute",
            json={},
            headers={"X-Company-ID": str(company_id), "Authorization": f"Bearer {user_id}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["run"]["status"] == "REVIEW"

    @pytest.mark.asyncio
    async def test_compute_with_dry_run_flag_returns_preview(self, db_session, client: AsyncClient, payroll_run, monkeypatch):
        """POST /compute?dry_run=true returns preview without state change."""
        company_id = payroll_run.company_id
        run_id = payroll_run.id
        user_id = uuid4()

        monkeypatch.setenv("X-Company-ID", str(company_id))

        response = await client.post(
            f"/api/v1/payroll/runs/{run_id}/compute?dry_run=true",
            json={},
            headers={"X-Company-ID": str(company_id), "Authorization": f"Bearer {user_id}"}
        )

        assert response.status_code == 200
        data = response.json()
        # In dry-run mode, run should still be DRAFT
        assert data["run"]["status"] == "DRAFT"
        # But preview payslips should be returned
        assert "preview_payslips" in data or "payslips" in data

    @pytest.mark.asyncio
    async def test_compute_non_draft_payroll_fails(self, db_session, client: AsyncClient, payroll_run, monkeypatch):
        """POST /compute on non-DRAFT run returns 409."""
        company_id = payroll_run.company_id
        run_id = payroll_run.id
        user_id = uuid4()

        # Move run to REVIEW manually
        payroll_run.status = PayrollStatus.REVIEW.value
        db_session.add(payroll_run)
        await db_session.commit()

        monkeypatch.setenv("X-Company-ID", str(company_id))

        response = await client.post(
            f"/api/v1/payroll/runs/{run_id}/compute",
            json={},
            headers={"X-Company-ID": str(company_id), "Authorization": f"Bearer {user_id}"}
        )

        assert response.status_code == 409, "Compute on non-DRAFT should return 409"


@pytest.mark.integration
class TestPayrollApprovalEndpoints:
    """Tests approve/reject workflow."""

    @pytest.mark.asyncio
    async def test_approve_review_payroll_transitions_to_approved(self, db_session, client: AsyncClient, payroll_run, monkeypatch):
        """POST /approve moves REVIEW → APPROVED."""
        company_id = payroll_run.company_id
        run_id = payroll_run.id
        user_id = uuid4()

        # Move to REVIEW first
        payroll_run.status = PayrollStatus.REVIEW.value
        db_session.add(payroll_run)
        await db_session.commit()

        monkeypatch.setenv("X-Company-ID", str(company_id))

        response = await client.post(
            f"/api/v1/payroll/runs/{run_id}/approve",
            json={},
            headers={"X-Company-ID": str(company_id), "Authorization": f"Bearer {user_id}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "APPROVED"
        assert data["approved_by"] is not None

    @pytest.mark.asyncio
    async def test_reject_review_payroll_transitions_to_draft(self, db_session, client: AsyncClient, payroll_run, monkeypatch):
        """POST /reject moves REVIEW → DRAFT."""
        company_id = payroll_run.company_id
        run_id = payroll_run.id
        user_id = uuid4()

        # Move to REVIEW first
        payroll_run.status = PayrollStatus.REVIEW.value
        db_session.add(payroll_run)
        await db_session.commit()

        monkeypatch.setenv("X-Company-ID", str(company_id))

        response = await client.post(
            f"/api/v1/payroll/runs/{run_id}/reject",
            json={"rejection_reason": "Recalculation needed"},
            headers={"X-Company-ID": str(company_id), "Authorization": f"Bearer {user_id}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DRAFT"

    @pytest.mark.asyncio
    async def test_approve_non_review_payroll_fails(self, db_session, client: AsyncClient, payroll_run, monkeypatch):
        """POST /approve on non-REVIEW run returns 409."""
        company_id = payroll_run.company_id
        run_id = payroll_run.id
        user_id = uuid4()

        # Stay in DRAFT
        assert payroll_run.status == PayrollStatus.DRAFT.value

        monkeypatch.setenv("X-Company-ID", str(company_id))

        response = await client.post(
            f"/api/v1/payroll/runs/{run_id}/approve",
            json={},
            headers={"X-Company-ID": str(company_id), "Authorization": f"Bearer {user_id}"}
        )

        assert response.status_code == 409, "Approve on non-REVIEW should return 409"


@pytest.mark.integration
class TestPayrollProcessEndpoint:
    """Tests POST /payroll/runs/{id}/process endpoint."""

    @pytest.mark.asyncio
    async def test_process_approved_payroll_creates_payslips_and_locks(self, db_session, client: AsyncClient, payroll_run, employee_salaries, monkeypatch):
        """POST /process creates payslips, locks them, moves to COMPLETED."""
        company_id = payroll_run.company_id
        run_id = payroll_run.id
        user_id = uuid4()

        # Move to APPROVED
        payroll_run.status = PayrollStatus.APPROVED.value
        payroll_run.approved_by = user_id
        db_session.add(payroll_run)
        await db_session.commit()

        monkeypatch.setenv("X-Company-ID", str(company_id))

        response = await client.post(
            f"/api/v1/payroll/runs/{run_id}/process",
            json={},
            headers={"X-Company-ID": str(company_id), "Authorization": f"Bearer {user_id}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"
        assert data["locked_at"] is not None

        # Verify payslips were created
        from app.models.payroll import Payslip
        from sqlalchemy import select
        payslips = await db_session.execute(
            select(Payslip).where(Payslip.payroll_run_id == run_id)
        )
        payslip_list = payslips.scalars().all()
        assert len(payslip_list) == len(employee_salaries), "Payslips should be created for all employees"

        # Verify payslips are locked
        for payslip in payslip_list:
            assert payslip.locked_at is not None, "Payslips should be locked after process"

    @pytest.mark.asyncio
    async def test_process_non_approved_payroll_fails(self, db_session, client: AsyncClient, payroll_run, monkeypatch):
        """POST /process on non-APPROVED run returns 409."""
        company_id = payroll_run.company_id
        run_id = payroll_run.id
        user_id = uuid4()

        # Stay in DRAFT
        assert payroll_run.status == PayrollStatus.DRAFT.value

        monkeypatch.setenv("X-Company-ID", str(company_id))

        response = await client.post(
            f"/api/v1/payroll/runs/{run_id}/process",
            json={},
            headers={"X-Company-ID": str(company_id), "Authorization": f"Bearer {user_id}"}
        )

        assert response.status_code == 409, "Process on non-APPROVED should return 409"


@pytest.mark.integration
class TestPayrollLockdownEndpoints:
    """Tests mark-paid and lock endpoints."""

    @pytest.mark.asyncio
    async def test_mark_paid_completed_payroll(self, db_session, client: AsyncClient, payroll_run, monkeypatch):
        """POST /mark-paid moves COMPLETED → PAID."""
        company_id = payroll_run.company_id
        run_id = payroll_run.id
        user_id = uuid4()

        # Move to COMPLETED
        payroll_run.status = PayrollStatus.COMPLETED.value
        db_session.add(payroll_run)
        await db_session.commit()

        monkeypatch.setenv("X-Company-ID", str(company_id))

        response = await client.post(
            f"/api/v1/payroll/runs/{run_id}/mark-paid",
            json={},
            headers={"X-Company-ID": str(company_id), "Authorization": f"Bearer {user_id}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PAID"

    @pytest.mark.asyncio
    async def test_lock_paid_payroll(self, db_session, client: AsyncClient, payroll_run, monkeypatch):
        """POST /lock moves PAID → LOCKED."""
        company_id = payroll_run.company_id
        run_id = payroll_run.id
        user_id = uuid4()

        # Move to PAID
        payroll_run.status = PayrollStatus.PAID.value
        db_session.add(payroll_run)
        await db_session.commit()

        monkeypatch.setenv("X-Company-ID", str(company_id))

        response = await client.post(
            f"/api/v1/payroll/runs/{run_id}/lock",
            json={},
            headers={"X-Company-ID": str(company_id), "Authorization": f"Bearer {user_id}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "LOCKED"


@pytest.mark.integration
class TestPayrollRetryOnFailure:
    """Tests retry workflow for FAILED payroll."""

    @pytest.mark.asyncio
    async def test_retry_failed_payroll_returns_to_draft(self, db_session, client: AsyncClient, payroll_run, monkeypatch):
        """POST /retry moves FAILED → DRAFT."""
        company_id = payroll_run.company_id
        run_id = payroll_run.id
        user_id = uuid4()

        # Move to FAILED
        payroll_run.status = PayrollStatus.FAILED.value
        payroll_run.exception_report = {
            "errors": ["Test error for retry"]
        }
        db_session.add(payroll_run)
        await db_session.commit()

        monkeypatch.setenv("X-Company-ID", str(company_id))

        response = await client.post(
            f"/api/v1/payroll/runs/{run_id}/retry",
            json={},
            headers={"X-Company-ID": str(company_id), "Authorization": f"Bearer {user_id}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DRAFT"
        # Exception report should be cleared on retry
        assert data.get("exception_report") is None or data["exception_report"] == {}


@pytest.mark.integration
class TestPayrollDataExportEndpoints:
    """Tests export endpoints (ECR, bank advice, etc.)."""

    @pytest.mark.asyncio
    async def test_ecr_file_export(self, db_session, client: AsyncClient, payroll_run, employee_salaries, monkeypatch):
        """GET /payroll/runs/{id}/ecr-file returns ECR format text file."""
        company_id = payroll_run.company_id
        run_id = payroll_run.id

        # Move to COMPLETED (ECR only available after completion)
        payroll_run.status = PayrollStatus.COMPLETED.value
        db_session.add(payroll_run)
        await db_session.commit()

        monkeypatch.setenv("X-Company-ID", str(company_id))

        response = await client.get(
            f"/api/v1/payroll/runs/{run_id}/ecr-file",
            headers={"X-Company-ID": str(company_id), "Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        # ECR file should have proper headers
        assert "Content-Disposition" in response.headers
        assert "attachment" in response.headers["Content-Disposition"]
        assert ".txt" in response.headers["Content-Disposition"]

    @pytest.mark.asyncio
    async def test_bank_advice_csv_export(self, db_session, client: AsyncClient, payroll_run, monkeypatch):
        """GET /payroll/runs/{id}/bank-advice returns CSV with employee accounts."""
        company_id = payroll_run.company_id
        run_id = payroll_run.id

        payroll_run.status = PayrollStatus.COMPLETED.value
        db_session.add(payroll_run)
        await db_session.commit()

        monkeypatch.setenv("X-Company-ID", str(company_id))

        response = await client.get(
            f"/api/v1/payroll/runs/{run_id}/bank-advice",
            headers={"X-Company-ID": str(company_id), "Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        assert "text/csv" in response.headers.get("Content-Type", "")


@pytest.mark.integration
class TestPayrollPermissions:
    """Tests role-based access control."""

    @pytest.mark.asyncio
    async def test_non_admin_cannot_approve_payroll(self, db_session, client: AsyncClient, payroll_run, monkeypatch):
        """Employee cannot approve payroll (403)."""
        company_id = payroll_run.company_id
        run_id = payroll_run.id

        payroll_run.status = PayrollStatus.REVIEW.value
        db_session.add(payroll_run)
        await db_session.commit()

        monkeypatch.setenv("X-Company-ID", str(company_id))

        # Mock non-admin user
        response = await client.post(
            f"/api/v1/payroll/runs/{run_id}/approve",
            json={},
            headers={
                "X-Company-ID": str(company_id),
                "Authorization": "Bearer non-admin-token",
                "X-User-Role": "EMPLOYEE"
            }
        )

        assert response.status_code == 403, "Non-admin should not be able to approve"

    @pytest.mark.asyncio
    async def test_non_admin_cannot_lock_payroll(self, db_session, client: AsyncClient, payroll_run, monkeypatch):
        """Employee cannot lock payroll (403)."""
        company_id = payroll_run.company_id
        run_id = payroll_run.id

        payroll_run.status = PayrollStatus.PAID.value
        db_session.add(payroll_run)
        await db_session.commit()

        monkeypatch.setenv("X-Company-ID", str(company_id))

        response = await client.post(
            f"/api/v1/payroll/runs/{run_id}/lock",
            json={},
            headers={
                "X-Company-ID": str(company_id),
                "Authorization": "Bearer non-admin-token",
                "X-User-Role": "EMPLOYEE"
            }
        )

        assert response.status_code == 403, "Non-admin should not be able to lock"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
