"""Template Application Service — Orchestrated Saga with Compensation.

Applies a region-specific onboarding template to a company by calling
leave-service and payroll-service internal APIs sequentially. On any step
failure, compensates by rolling back already-created resources before
returning a PARTIAL/FAILED status.

Retry policy: 5 attempts with exponential backoff (1s → 16s max).
Circuit breaker: opens after 3 failures, recovers after 30s.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

try:
    from circuitbreaker import circuit
    HAS_CIRCUIT_BREAKER = True
except ImportError:
    HAS_CIRCUIT_BREAKER = False
    def circuit(*args, **kwargs):  # no-op decorator fallback
        def decorator(fn):
            return fn
        return decorator

from app.core.config import settings
from app.core.internal_auth import create_service_token
from app.models.onboarding import TemplateApplicationLog, OnboardingTemplate

logger = logging.getLogger(__name__)

_LEAVE_SEED_URL = "{leave_url}/api/v1/internal/leave-types/bulk-seed"
_LEAVE_ROLLBACK_URL = "{leave_url}/api/v1/internal/leave-types/bulk-rollback"
_PAYROLL_SEED_URL = "{payroll_url}/api/v1/internal/salary-structures/seed"
_PAYROLL_ROLLBACK_URL = "{payroll_url}/api/v1/internal/salary-structures/rollback"

_HTTP_TIMEOUT = 10.0


def _internal_headers() -> dict:
    """Generate fresh JWT service token headers for each request."""
    token = create_service_token("onboarding-service")
    return {"X-Service-Token": token, "X-Internal-Token": token}


class SagaStepState:
    def __init__(self, step: str):
        self.step = step
        self.status = "PENDING"
        self.result: dict = {}
        self.error: Optional[str] = None

    def to_dict(self) -> dict:
        return {"step": self.step, "status": self.status, "result": self.result, "error": self.error}


class TemplateApplicationError(Exception):
    """Raised when a saga step fails and cannot be retried."""
    def __init__(self, step: str, detail: str):
        self.step = step
        self.detail = detail
        super().__init__(f"Saga step '{step}' failed: {detail}")


async def _http_post(client: httpx.AsyncClient, url: str, payload: dict) -> httpx.Response:
    return await client.post(url, json=payload, headers=_INTERNAL_HEADERS, timeout=_HTTP_TIMEOUT)


async def _http_delete(client: httpx.AsyncClient, url: str, payload: dict) -> httpx.Response:
    return await client.request("DELETE", url, json=payload, headers=_INTERNAL_HEADERS, timeout=_HTTP_TIMEOUT)


if HAS_CIRCUIT_BREAKER:
    _http_post = circuit(failure_threshold=3, recovery_timeout=30)(_http_post)
    _http_delete = circuit(failure_threshold=3, recovery_timeout=30)(_http_delete)

_retry_decorator = retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=16),
    retry=retry_if_exception_type(httpx.TransportError),
    reraise=True,
)
_post_with_retry = _retry_decorator(_http_post)
_delete_with_retry = _retry_decorator(_http_delete)


class TemplateApplicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def apply_template(self, company_id: UUID, region: str) -> dict:
        """Apply the template for the given region to the company.

        Returns a dict with status (COMPLETED/PARTIAL/FAILED), log_id, and saga_steps.
        Raises HTTPException for invalid region or already-completed application.
        """
        # Check for existing COMPLETED log
        existing = await self.db.execute(
            select(TemplateApplicationLog).where(
                TemplateApplicationLog.company_id == company_id,
                TemplateApplicationLog.status == "COMPLETED",
            )
        )
        if existing.scalars().first():
            return {"status": "ALREADY_APPLIED", "message": "Template already successfully applied for this company"}

        # Load template from DB
        template = await self._load_template(region)
        defaults = json.loads(template.template_json).get("defaults", {})

        # Create audit log entry
        log = TemplateApplicationLog(
            company_id=company_id,
            template_region=region,
            status="PENDING",
            applied_at=datetime.now(timezone.utc),
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)

        steps: list[SagaStepState] = []
        created_leave_ids: list[str] = []
        created_payroll_id: Optional[str] = None

        try:
            # ── Step 1: Seed leave types ─────────────────────────────────
            if "leave_types" in defaults:
                step = SagaStepState("leave_types")
                steps.append(step)
                leave_items = [
                    {"name": lt["name"], "days_allowed": lt["days"], "requires_approval": True}
                    for lt in defaults["leave_types"]
                ]
                try:
                    async with httpx.AsyncClient() as client:
                        resp = await _post_with_retry(client, _LEAVE_SEED_URL.format(leave_url=settings.LEAVE_SERVICE_URL), {
                            "company_id": str(company_id),
                            "leave_types": leave_items,
                        })
                    if resp.status_code not in (200, 201):
                        raise TemplateApplicationError("leave_types", f"HTTP {resp.status_code}: {resp.text[:200]}")
                    body = resp.json()
                    created_leave_ids = [str(i) for i in body.get("created_ids", [])]
                    step.status = "COMPLETED"
                    step.result = {"created_ids": created_leave_ids, "skipped": body.get("skipped", [])}
                except TemplateApplicationError:
                    raise
                except Exception as exc:
                    raise TemplateApplicationError("leave_types", str(exc)) from exc

            # ── Step 2: Seed salary structure ────────────────────────────
            if "salary_structure" in defaults:
                step = SagaStepState("salary_structure")
                steps.append(step)
                ss = defaults["salary_structure"]
                try:
                    async with httpx.AsyncClient() as client:
                        resp = await _post_with_retry(client, _PAYROLL_SEED_URL.format(payroll_url=settings.PAYROLL_SERVICE_URL), {
                            "company_id": str(company_id),
                            "name": "Default Salary Structure",
                            "description": f"Auto-seeded from {region} onboarding template",
                            "basic_pct": ss.get("basic_pct", 50.0),
                            "hra_pct": ss.get("hra_pct", 20.0),
                            "allowances_pct": ss.get("allowances_pct", 15.0),
                            "pf_pct": ss.get("pf_pct", 12.0),
                            "esi_pct": ss.get("esi_pct", 1.75),
                            "professional_tax": ss.get("professional_tax", 200.0),
                        })
                    if resp.status_code not in (200, 201):
                        raise TemplateApplicationError("salary_structure", f"HTTP {resp.status_code}: {resp.text[:200]}")
                    body = resp.json()
                    if not body.get("skipped"):
                        created_payroll_id = str(body.get("id")) if body.get("id") else None
                    step.status = "COMPLETED"
                    step.result = {"id": body.get("id"), "skipped": body.get("skipped", False)}
                except TemplateApplicationError:
                    raise
                except Exception as exc:
                    raise TemplateApplicationError("salary_structure", str(exc)) from exc

            # All steps succeeded
            log.status = "COMPLETED"
            log.completed_at = datetime.now(timezone.utc)
            log.saga_steps_json = json.dumps([s.to_dict() for s in steps])
            log.result_json = json.dumps({"created_leave_ids": created_leave_ids, "created_payroll_id": created_payroll_id})
            await self.db.commit()

            logger.info("Template applied successfully", extra={"company_id": str(company_id), "region": region})
            return {
                "status": "COMPLETED",
                "log_id": str(log.id),
                "saga_steps": [s.to_dict() for s in steps],
            }

        except TemplateApplicationError as err:
            logger.error(f"Template application failed at step '{err.step}': {err.detail}", extra={"company_id": str(company_id)})
            log.status = "COMPENSATING"
            log.saga_steps_json = json.dumps([s.to_dict() for s in steps])
            await self.db.commit()

            # Compensate: rollback already-created resources
            compensation_errors: list[str] = []
            if created_leave_ids:
                try:
                    async with httpx.AsyncClient() as client:
                        await _delete_with_retry(client, _LEAVE_ROLLBACK_URL.format(leave_url=settings.LEAVE_SERVICE_URL), {
                            "company_id": str(company_id),
                            "leave_type_ids": created_leave_ids,
                        })
                    logger.info("Leave types rolled back", extra={"company_id": str(company_id), "ids": created_leave_ids})
                except Exception as comp_err:
                    compensation_errors.append(f"leave_rollback: {comp_err}")
                    logger.error(f"Failed to rollback leave types: {comp_err}", extra={"company_id": str(company_id)})

            if created_payroll_id:
                try:
                    async with httpx.AsyncClient() as client:
                        await _delete_with_retry(client, _PAYROLL_ROLLBACK_URL.format(payroll_url=settings.PAYROLL_SERVICE_URL), {
                            "company_id": str(company_id),
                            "salary_structure_id": created_payroll_id,
                        })
                    logger.info("Salary structure rolled back", extra={"company_id": str(company_id), "id": created_payroll_id})
                except Exception as comp_err:
                    compensation_errors.append(f"payroll_rollback: {comp_err}")
                    logger.error(f"Failed to rollback salary structure: {comp_err}", extra={"company_id": str(company_id)})

            final_status = "COMPENSATED" if not compensation_errors else "FAILED"
            log.status = final_status
            log.result_json = json.dumps({
                "failed_step": err.step,
                "error": err.detail,
                "compensation_errors": compensation_errors,
            })
            await self.db.commit()

            return {
                "status": "PARTIAL",
                "log_id": str(log.id),
                "failed_step": err.step,
                "error": err.detail,
                "compensation_status": final_status,
                "saga_steps": [s.to_dict() for s in steps],
            }

    async def _load_template(self, region: str) -> OnboardingTemplate:
        result = await self.db.execute(
            select(OnboardingTemplate).where(OnboardingTemplate.region == region)
        )
        template = result.scalars().first()
        if not template:
            # Fall back to default
            result = await self.db.execute(
                select(OnboardingTemplate).where(OnboardingTemplate.region == "default")
            )
            template = result.scalars().first()
        if not template:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"No template found for region '{region}' and no default template available")
        return template
