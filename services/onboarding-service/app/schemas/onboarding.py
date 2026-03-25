from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class StepResponse(BaseModel):
    step_key: str
    label: str
    order: int
    status: str
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OnboardingStatusResponse(BaseModel):
    company_id: UUID
    status: str
    steps: list[StepResponse]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percent: int = 0

    class Config:
        from_attributes = True


class CompleteStepRequest(BaseModel):
    step_key: str
    skipped: bool = False


class TemplateResponse(BaseModel):
    id: UUID
    category: str
    region: str
    name: str
    template_json: str

    class Config:
        from_attributes = True


class RetryStepRequest(BaseModel):
    step_key: str
