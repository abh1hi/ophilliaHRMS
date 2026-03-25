import asyncio
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.api.v1.dependencies import get_current_user, require_role, TokenUser
from app.core.constants import UserRole
from app.schemas.onboarding import (
    OnboardingStatusResponse,
    StepResponse,
    CompleteStepRequest,
    TemplateResponse,
    RetryStepRequest,
)
from app.services.onboarding_service import OnboardingService

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
        asyncio.create_task(publisher.publish(event_type, {
            "company_id": current_user.company_id,
            "step_key": body.step_key,
            "progress_percent": progress,
            "user_id": current_user.id,
        }))

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
        asyncio.create_task(publisher.publish("onboarding.wizard_completed", {
            "company_id": current_user.company_id,
            "progress_percent": progress,
            "user_id": current_user.id,
        }))

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
