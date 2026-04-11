"""Internal endpoints — service-to-service only.

Authenticated via X-Service-Token JWT (HS256, 5-min TTL).
Used by onboarding-service for template application saga.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.future import select
from sqlalchemy import delete
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.payroll import SalaryStructure
from app.core.config import settings
from app.core.internal_auth import verify_service_jwt
from app.db.session import AsyncSessionLocal

router = APIRouter(prefix="/internal", tags=["internal"])


class SalaryStructureSeedRequest(BaseModel):
    company_id: UUID
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    basic_pct: Decimal = Field(50.0, ge=0, le=100)
    hra_pct: Decimal = Field(20.0, ge=0, le=100)
    allowances_pct: Decimal = Field(15.0, ge=0, le=100)
    pf_pct: Decimal = Field(12.0, ge=0, le=100)
    esi_pct: Decimal = Field(1.75, ge=0, le=100)
    professional_tax: Decimal = Field(200.0, ge=0)


class SalaryStructureSeedResponse(BaseModel):
    id: Optional[UUID] = None
    skipped: bool = False
    message: str = ""


class SalaryStructureRollbackRequest(BaseModel):
    company_id: UUID
    salary_structure_id: UUID


@router.post(
    "/salary-structures/seed",
    response_model=SalaryStructureSeedResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_service_jwt)],
)
async def seed_salary_structure(body: SalaryStructureSeedRequest):
    """Idempotent create salary structure for a company.

    Used by onboarding-service template application saga.
    Skips creation if a salary structure with the same name already exists for the company.
    """
    async with AsyncSessionLocal() as db:
        existing = await db.execute(
            select(SalaryStructure).where(
                SalaryStructure.company_id == body.company_id,
                SalaryStructure.name == body.name,
                SalaryStructure.is_active == 1,
            )
        )
        obj = existing.scalars().first()
        if obj:
            return SalaryStructureSeedResponse(id=obj.id, skipped=True, message="Already exists")

        structure = SalaryStructure(
            company_id=body.company_id,
            name=body.name,
            description=body.description,
            basic_pct=body.basic_pct,
            hra_pct=body.hra_pct,
            allowances_pct=body.allowances_pct,
            pf_pct=body.pf_pct,
            esi_pct=body.esi_pct,
            professional_tax=body.professional_tax,
            is_active=1,
        )
        db.add(structure)
        await db.commit()
        await db.refresh(structure)

        return SalaryStructureSeedResponse(id=structure.id, skipped=False, message="Created")


@router.delete(
    "/salary-structures/rollback",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_service_jwt)],
)
async def rollback_salary_structure(body: SalaryStructureRollbackRequest):
    """Delete a salary structure by ID for a company (saga compensation).

    Used by onboarding-service template application saga on failure.
    Only deletes if the structure belongs to the given company_id (safety check).
    """
    async with AsyncSessionLocal() as db:
        await db.execute(
            delete(SalaryStructure).where(
                SalaryStructure.id == body.salary_structure_id,
                SalaryStructure.company_id == body.company_id,
            )
        )
        await db.commit()
