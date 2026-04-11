"""Daily reconciliation job — verifies onboarding_status matches observed reality.

Runs once per day at 02:00 UTC. For each company with a non-terminal onboarding
state, calls domain-service internal APIs to count actual resources, then:
  - If a step shows PENDING but the resource already exists → mark COMPLETED (auto-fix)
  - If the overall state is FULLY_ONBOARDED but some step is still PENDING → set back to IN_PROGRESS
  - Logs all mismatches at WARNING; unresolvable mismatches are left for admin review

This job is a safety net — not a substitute for correct event handling.
Feature flag: ENABLE_EVENT_DRIVEN_ONBOARDING must be True for auto-corrections to apply;
without it the job only logs mismatches.
"""
import asyncio
import logging
from datetime import datetime, timezone, time as dtime

import httpx

from app.core.config import settings
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

_INTERNAL_TIMEOUT = 5.0


def _service_headers() -> dict:
    """Generate fresh JWT service token for internal API calls."""
    from app.core.internal_auth import create_service_token
    token = create_service_token("onboarding-service")
    return {"X-Service-Token": token}


async def _count_leave_types(company_id: str) -> int | None:
    """Return number of leave types for company, or None if unreachable."""
    url = f"{settings.LEAVE_SERVICE_URL}/api/v1/internal/leave-types/count"
    try:
        async with httpx.AsyncClient(timeout=_INTERNAL_TIMEOUT) as client:
            resp = await client.get(url, params={"company_id": company_id}, headers=_service_headers())
        if resp.status_code == 200:
            return resp.json().get("count", 0)
    except Exception as exc:
        logger.debug(f"Could not reach leave-service for company {company_id}: {exc}")
    return None


async def _count_salary_structures(company_id: str) -> int | None:
    """Return number of active salary structures for company, or None if unreachable."""
    url = f"{settings.PAYROLL_SERVICE_URL}/api/v1/internal/salary-structures/count"
    try:
        async with httpx.AsyncClient(timeout=_INTERNAL_TIMEOUT) as client:
            resp = await client.get(url, params={"company_id": company_id}, headers=_service_headers())
        if resp.status_code == 200:
            return resp.json().get("count", 0)
    except Exception as exc:
        logger.debug(f"Could not reach payroll-service for company {company_id}: {exc}")
    return None


async def _reconcile_company(db, state) -> list[str]:
    """Check one company's onboarding state against domain-service reality.

    Returns a list of mismatch descriptions (empty = all good).
    """
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.onboarding import OnboardingState, OnboardingStep
    from app.core.constants import StepStatus

    mismatches: list[str] = []
    company_id = str(state.company_id)

    # Re-load steps (state may be a bare row without relationship loaded)
    result = await db.execute(
        select(OnboardingState)
        .options(selectinload(OnboardingState.steps))
        .where(OnboardingState.id == state.id)
    )
    full_state = result.scalars().first()
    if not full_state:
        return mismatches

    step_map = {s.step_key: s for s in full_state.steps}

    # Check leave_types step
    leave_step = step_map.get("leave_types")
    if leave_step and leave_step.status == StepStatus.PENDING.value:
        count = await _count_leave_types(company_id)
        if count is not None and count > 0:
            mismatches.append(f"leave_types: step PENDING but {count} leave types exist")
            if settings.ENABLE_EVENT_DRIVEN_ONBOARDING:
                leave_step.status = StepStatus.COMPLETED.value
                leave_step.completed_at = datetime.now(timezone.utc)
                logger.info(f"Auto-corrected leave_types step for company {company_id}")

    # Check salary_structure step
    salary_step = step_map.get("salary_structure")
    if salary_step and salary_step.status == StepStatus.PENDING.value:
        count = await _count_salary_structures(company_id)
        if count is not None and count > 0:
            mismatches.append(f"salary_structure: step PENDING but {count} structures exist")
            if settings.ENABLE_EVENT_DRIVEN_ONBOARDING:
                salary_step.status = StepStatus.COMPLETED.value
                salary_step.completed_at = datetime.now(timezone.utc)
                logger.info(f"Auto-corrected salary_structure step for company {company_id}")

    # Check state consistency: FULLY_ONBOARDED but steps still PENDING
    if full_state.status == "FULLY_ONBOARDED":
        pending_steps = [s.step_key for s in full_state.steps if s.status == StepStatus.PENDING.value]
        if pending_steps:
            mismatches.append(f"state=FULLY_ONBOARDED but steps still PENDING: {pending_steps}")
            if settings.ENABLE_EVENT_DRIVEN_ONBOARDING:
                full_state.status = "IN_PROGRESS"
                logger.warning(f"Reverted company {company_id} from FULLY_ONBOARDED to IN_PROGRESS due to pending steps")

    return mismatches


async def run_reconciliation() -> None:
    """Run one reconciliation pass over all non-terminal onboarding states."""
    from sqlalchemy import select
    from app.models.onboarding import OnboardingState

    terminal_statuses = {"FULLY_ONBOARDED", "WIZARD_COMPLETE"}

    logger.info("Reconciliation job started", extra={"service_task": "reconciliation"})
    total = 0
    mismatch_count = 0

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(OnboardingState).where(OnboardingState.status.not_in(terminal_statuses))
        )
        states = result.scalars().all()

        for state in states:
            total += 1
            try:
                mismatches = await _reconcile_company(db, state)
                if mismatches:
                    mismatch_count += 1
                    for m in mismatches:
                        logger.warning(
                            f"Reconciliation mismatch — company {state.company_id}: {m}",
                            extra={"service_task": "reconciliation", "company_id": str(state.company_id)},
                        )
            except Exception as exc:
                logger.error(
                    f"Reconciliation error for company {state.company_id}: {exc}",
                    extra={"service_task": "reconciliation", "company_id": str(state.company_id)},
                )

        if mismatch_count > 0:
            await db.commit()

    logger.info(
        f"Reconciliation complete — checked {total} companies, found {mismatch_count} mismatches",
        extra={"service_task": "reconciliation"},
    )


async def run_reconciliation_loop() -> None:
    """Asyncio loop: runs reconciliation daily at 02:00 UTC."""
    logger.info("Reconciliation loop started — will run daily at 02:00 UTC")
    while True:
        try:
            now = datetime.now(timezone.utc)
            # Next 02:00 UTC
            target = datetime.combine(now.date(), dtime(2, 0), tzinfo=timezone.utc)
            if now >= target:
                target = target.replace(day=target.day + 1)
            wait_seconds = (target - now).total_seconds()
            logger.debug(f"Next reconciliation in {wait_seconds:.0f}s ({target.isoformat()})")
            await asyncio.sleep(wait_seconds)
            await run_reconciliation()
        except asyncio.CancelledError:
            logger.info("Reconciliation loop cancelled — shutting down")
            return
        except Exception as exc:
            logger.error(f"Reconciliation loop error: {exc}", extra={"service_task": "reconciliation"})
            await asyncio.sleep(60)  # Back off 1 minute on unexpected errors
