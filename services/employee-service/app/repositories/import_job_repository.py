from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.import_job import ImportJob


def _naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ImportJobRepository:
    def __init__(self, db: AsyncSession, company_id: UUID):
        self.db = db
        self.company_id = company_id

    async def create(self, **kwargs) -> ImportJob:
        job = ImportJob(company_id=self.company_id, **kwargs)
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_by_id(self, job_id: UUID) -> Optional[ImportJob]:
        result = await self.db.execute(
            select(ImportJob).where(
                ImportJob.id == job_id,
                ImportJob.company_id == self.company_id,
            )
        )
        return result.scalars().first()

    async def get_by_idempotency_key(self, key: str) -> Optional[ImportJob]:
        result = await self.db.execute(
            select(ImportJob).where(
                ImportJob.idempotency_key == key,
                ImportJob.company_id == self.company_id,
            )
        )
        return result.scalars().first()

    async def list_by_company(self, limit: int = 50, offset: int = 0) -> List[ImportJob]:
        result = await self.db.execute(
            select(ImportJob)
            .where(ImportJob.company_id == self.company_id)
            .order_by(ImportJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update_status(self, job_id: UUID, status: str, completed: bool = False):
        values = {"status": status}
        if completed:
            values["completed_at"] = _naive_utcnow()
        await self.db.execute(
            update(ImportJob).where(ImportJob.id == job_id).values(**values)
        )
        await self.db.commit()

    async def update_progress(
        self,
        job_id: UUID,
        succeeded_rows: int,
        failed_rows: int,
        skipped_rows: int,
        status: Optional[str] = None,
        error_log: Optional[list] = None,
        auto_corrections: Optional[list] = None,
    ):
        values: dict = {
            "succeeded_rows": succeeded_rows,
            "failed_rows": failed_rows,
            "skipped_rows": skipped_rows,
        }
        if status:
            values["status"] = status
        if status in ("completed", "failed"):
            values["completed_at"] = _naive_utcnow()
        if error_log is not None:
            values["error_log"] = error_log
        if auto_corrections is not None:
            values["auto_corrections"] = auto_corrections
        await self.db.execute(
            update(ImportJob).where(ImportJob.id == job_id).values(**values)
        )
        await self.db.commit()
