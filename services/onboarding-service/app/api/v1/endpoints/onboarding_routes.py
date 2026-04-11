import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.api.v1.dependencies import get_current_user, require_role, TokenUser
from app.core.constants import UserRole
from app.core.config import settings
from app.core.internal_auth import verify_service_jwt
from app.schemas.onboarding import (
    OnboardingStatusResponse,
    StepResponse,
    CompleteStepRequest,
    TemplateResponse,
    RetryStepRequest,
    ApplyTemplateRequest,
    ApplyTemplateResponse,
)
from app.services.onboarding_service import OnboardingService
from app.services.template_application_service import TemplateApplicationService

router = APIRouter()


@router.get("/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    current_user: TokenUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get onboarding state + steps for the current user's company."""
    service = OnboardingService(db)
    state = await service.get_status(UUID(current_user.company_id))
    progress = service.calculate_progress(state)

    return OnboardingStatusResponse(
        company_id=state.company_id,
        status=state.status,
        steps=[
            StepResponse(
                step_key=s.step_key,
                label=s.label,
                order=s.order,
                status=s.status,
                completed_at=s.completed_at,
            )
            for s in sorted(state.steps, key=lambda x: x.order)
        ],
        started_at=state.started_at,
        completed_at=state.completed_at,
        progress_percent=progress,
    )


@router.post("/complete-step", response_model=OnboardingStatusResponse)
async def complete_step(
    request: Request,
    body: CompleteStepRequest,
    current_user: TokenUser = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    db: AsyncSession = Depends(get_db),
):
    """Mark a step as completed or skipped."""
    service = OnboardingService(db)
    state = await service.complete_step(UUID(current_user.company_id), body.step_key, body.skipped)
    progress = service.calculate_progress(state)

    # Publish analytics event (fire-and-forget)
    publisher = request.app.state.event_publisher
    if publisher:
        event_type = "onboarding.step_skipped" if body.skipped else "onboarding.step_completed"
        _task = asyncio.create_task(publisher.publish(event_type, {
            "company_id": current_user.company_id,
            "step_key": body.step_key,
            "progress_percent": progress,
            "user_id": current_user.id,
        }))
        request.state._bg_tasks = getattr(request.state, "_bg_tasks", set())
        request.state._bg_tasks.add(_task)
        _task.add_done_callback(request.state._bg_tasks.discard)

    # Publish onboarding.completed when all steps done (Phase 1.4)
    if state.status == "FULLY_ONBOARDED" and publisher:
        _task = asyncio.create_task(publisher.publish("onboarding.completed", {
            "company_id": current_user.company_id,
            "user_id": current_user.id,
        }))
        request.state._bg_tasks = getattr(request.state, "_bg_tasks", set())
        request.state._bg_tasks.add(_task)
        _task.add_done_callback(request.state._bg_tasks.discard)

    return OnboardingStatusResponse(
        company_id=state.company_id,
        status=state.status,
        steps=[
            StepResponse(step_key=s.step_key, label=s.label, order=s.order, status=s.status, completed_at=s.completed_at)
            for s in sorted(state.steps, key=lambda x: x.order)
        ],
        started_at=state.started_at,
        completed_at=state.completed_at,
        progress_percent=progress,
    )


@router.post("/complete-wizard", response_model=OnboardingStatusResponse)
async def complete_wizard(
    request: Request,
    current_user: TokenUser = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Advance onboarding to WIZARD_COMPLETE status."""
    service = OnboardingService(db)
    state = await service.complete_wizard(UUID(current_user.company_id))
    progress = service.calculate_progress(state)

    # Publish analytics event
    publisher = request.app.state.event_publisher
    if publisher:
        _task = asyncio.create_task(publisher.publish("onboarding.wizard_completed", {
            "company_id": current_user.company_id,
            "progress_percent": progress,
            "user_id": current_user.id,
        }))
        request.state._bg_tasks = getattr(request.state, "_bg_tasks", set())
        request.state._bg_tasks.add(_task)
        _task.add_done_callback(request.state._bg_tasks.discard)

    return OnboardingStatusResponse(
        company_id=state.company_id,
        status=state.status,
        steps=[
            StepResponse(step_key=s.step_key, label=s.label, order=s.order, status=s.status, completed_at=s.completed_at)
            for s in sorted(state.steps, key=lambda x: x.order)
        ],
        started_at=state.started_at,
        completed_at=state.completed_at,
        progress_percent=progress,
    )


@router.post("/retry-step/{step_key}", response_model=OnboardingStatusResponse)
async def retry_step(
    step_key: str,
    current_user: TokenUser = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Reset a failed/completed step back to PENDING for retry."""
    service = OnboardingService(db)
    state = await service.retry_step(UUID(current_user.company_id), step_key)
    progress = service.calculate_progress(state)

    return OnboardingStatusResponse(
        company_id=state.company_id,
        status=state.status,
        steps=[
            StepResponse(step_key=s.step_key, label=s.label, order=s.order, status=s.status, completed_at=s.completed_at)
            for s in sorted(state.steps, key=lambda x: x.order)
        ],
        started_at=state.started_at,
        completed_at=state.completed_at,
        progress_percent=progress,
    )


@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates(
    category: str | None = Query(None),
    region: str | None = Query(None),
    current_user: TokenUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List available seed templates, optionally filtered by category and region."""
    service = OnboardingService(db)
    templates = await service.list_templates(category, region)
    return templates


@router.post("/apply-template", response_model=ApplyTemplateResponse, status_code=200)
async def apply_template(
    request: Request,
    body: ApplyTemplateRequest,
    current_user: TokenUser = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Apply a region-specific onboarding template to the company.

    Orchestrated saga: creates leave types + salary structure via internal APIs.
    On partial failure, compensates by rolling back already-created resources.
    Returns COMPLETED, PARTIAL, or ALREADY_APPLIED status.
    Gated by ENABLE_TEMPLATE_APPLICATION feature flag.
    """
    if not settings.ENABLE_TEMPLATE_APPLICATION:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Template application is not enabled in this environment",
        )
    service = TemplateApplicationService(db)
    result = await service.apply_template(UUID(current_user.company_id), body.region)
    return ApplyTemplateResponse(**result)


# ── Internal endpoint (service-to-service) ───────────────────────────────────

@router.get(
    "/internal/status/{company_id}",
    dependencies=[Depends(verify_service_jwt)],
)
async def internal_onboarding_status(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return onboarding status for a company — internal use only.

    Called by auth-service post_login_context to determine COMPLETE_ONBOARDING action.
    Protected by X-Service-Token JWT.
    """
    service = OnboardingService(db)
    state = await service.get_status(company_id)
    return {"company_id": str(company_id), "status": state.status}
