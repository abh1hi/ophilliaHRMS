import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.onboarding import OnboardingState, OnboardingStep, OnboardingTemplate
from app.core.constants import OnboardingStatus, StepStatus, DEFAULT_STEPS

logger = logging.getLogger(__name__)


class OnboardingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_status(self, company_id: UUID) -> OnboardingState:
        result = await self.db.execute(
            select(OnboardingState)
            .options(selectinload(OnboardingState.steps))
            .where(OnboardingState.company_id == company_id)
        )
        state = result.scalars().first()
        if state:
            return state

        # Initialize fresh onboarding
        state = OnboardingState(
            company_id=company_id,
            status=OnboardingStatus.NOT_STARTED.value,
        )
        self.db.add(state)
        await self.db.flush()

        for step_def in DEFAULT_STEPS:
            step = OnboardingStep(
                onboarding_id=state.id,
                step_key=step_def["step_key"],
                label=step_def["label"],
                order=step_def["order"],
                status=StepStatus.PENDING.value,
            )
            self.db.add(step)

        await self.db.commit()
        await self.db.refresh(state)

        # Reload with steps
        result = await self.db.execute(
            select(OnboardingState)
            .options(selectinload(OnboardingState.steps))
            .where(OnboardingState.id == state.id)
        )
        return result.scalars().first()

    async def get_status(self, company_id: UUID) -> OnboardingState:
        state = await self.get_or_create_status(company_id)
        return state

    def calculate_progress(self, state: OnboardingState) -> int:
        if not state.steps:
            return 0
        done = sum(1 for s in state.steps if s.status in (StepStatus.COMPLETED.value, StepStatus.SKIPPED.value))
        return round((done / len(state.steps)) * 100)

    async def complete_step(self, company_id: UUID, step_key: str, skipped: bool = False) -> OnboardingState:
        state = await self.get_or_create_status(company_id)

        step = next((s for s in state.steps if s.step_key == step_key), None)
        if not step:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Step '{step_key}' not found")

        step.status = StepStatus.SKIPPED.value if skipped else StepStatus.COMPLETED.value
        step.completed_at = datetime.now(timezone.utc)

        # Update overall status
        if state.status == OnboardingStatus.NOT_STARTED.value:
            state.status = OnboardingStatus.IN_PROGRESS.value
            state.started_at = datetime.now(timezone.utc)

        # Check if all steps done
        all_done = all(
            s.status in (StepStatus.COMPLETED.value, StepStatus.SKIPPED.value)
            for s in state.steps
        )
        if all_done:
            state.status = OnboardingStatus.FULLY_ONBOARDED.value
            state.completed_at = datetime.now(timezone.utc)

        state.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(state)

        logger.info(
            f"Step '{step_key}' marked {'skipped' if skipped else 'completed'}",
            extra={"service_task": "complete_step", "company_id": str(company_id), "step_key": step_key},
        )

        return state

    async def complete_wizard(self, company_id: UUID) -> OnboardingState:
        state = await self.get_or_create_status(company_id)
        state.status = OnboardingStatus.WIZARD_COMPLETE.value
        state.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(state)

        logger.info(
            "Wizard marked complete",
            extra={"service_task": "complete_wizard", "company_id": str(company_id)},
        )
        return state

    async def retry_step(self, company_id: UUID, step_key: str) -> OnboardingState:
        state = await self.get_or_create_status(company_id)
        step = next((s for s in state.steps if s.step_key == step_key), None)
        if not step:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Step '{step_key}' not found")

        step.status = StepStatus.PENDING.value
        step.completed_at = None
        state.updated_at = datetime.now(timezone.utc)

        if state.status == OnboardingStatus.FULLY_ONBOARDED.value:
            state.status = OnboardingStatus.IN_PROGRESS.value
            state.completed_at = None

        await self.db.commit()
        await self.db.refresh(state)

        logger.info(
            f"Step '{step_key}' reset for retry",
            extra={"service_task": "retry_step", "company_id": str(company_id), "step_key": step_key},
        )
        return state

    async def list_templates(self, category: str | None = None, region: str | None = None) -> list[OnboardingTemplate]:
        query = select(OnboardingTemplate)
        if category:
            query = query.where(OnboardingTemplate.category == category)
        if region:
            query = query.where(OnboardingTemplate.region == region)
        result = await self.db.execute(query)
        return list(result.scalars().all())
