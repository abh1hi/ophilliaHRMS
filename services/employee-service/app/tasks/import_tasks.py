"""
Celery task: process_bulk_import

Processes bulk employee import jobs in chunks of 500 rows.
- Per-chunk transaction: BEGIN → process 500 → COMMIT (partial success preserved on failure)
- Retries up to 3 times with exponential backoff on unexpected errors
- Updates ImportJob progress after each chunk
- dry_run=True: validates + checks DB for duplicates but makes NO writes
- Layer 3 (DB) business validation is applied here: duplicate email strategy, employee_code uniqueness
"""
import asyncio
import logging
from datetime import datetime, date, timezone
from typing import Any
from uuid import UUID

from celery import Task
from pydantic import ValidationError

from app.tasks.celery_app import celery_app

# Must import all models before any SQLAlchemy mapper configuration runs.
# Celery workers don't boot via the FastAPI app, so they won't auto-discover
# related models through the normal app startup path.
import app.models  # noqa: F401  — side-effect: registers all ORM classes

logger = logging.getLogger(__name__)

CHUNK_SIZE = 500


def _naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def _run_import(
    job_id: str,
    rows: list[dict],
    company_id: str,
    dry_run: bool,
    duplicate_strategy: str,
) -> None:
    """Async core: runs inside asyncio.run() from the Celery task."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.db.session import AsyncSessionLocal
    from app.models.employee import Employee
    from app.repositories.employee_repository import EmployeeRepository
    from app.repositories.import_job_repository import ImportJobRepository
    from app.schemas.employee import BulkEmployeeImportItem, EmployeeUpdate as _EU

    job_uuid = UUID(job_id)
    company_uuid = UUID(company_id)

    # Open a dedicated session for progress updates (separate from per-chunk sessions)
    async with AsyncSessionLocal() as progress_session:
        progress_session.info["company_id"] = company_id
        job_repo = ImportJobRepository(progress_session, company_uuid)

        await job_repo.update_status(job_uuid, "processing")

        total = len(rows)
        succeeded = 0
        failed = 0
        skipped = 0
        error_log: list[dict] = []

        # Process in chunks of CHUNK_SIZE
        for chunk_start in range(0, total, CHUNK_SIZE):
            chunk = rows[chunk_start: chunk_start + CHUNK_SIZE]

            # Each chunk gets its own transaction — failure in one chunk does NOT
            # roll back previously committed chunks.
            async with AsyncSessionLocal() as db:
                db.info["company_id"] = company_id
                emp_repo = EmployeeRepository(db)

                chunk_succeeded = 0
                chunk_failed = 0
                chunk_skipped = 0

                for local_idx, raw in enumerate(chunk):
                    abs_row = chunk_start + local_idx

                    # ── Pydantic schema validation (Layer 1 — redundant but safe) ──
                    try:
                        # Coerce numeric values to strings for non-numeric fields
                        for k, v in list(raw.items()):
                            if isinstance(v, (int, float)) and k not in (
                                "joining_salary", "last_drawn_salary"
                            ):
                                raw[k] = str(int(v)) if isinstance(v, float) and v == int(v) else str(v)

                        item = BulkEmployeeImportItem(**raw)
                    except (ValidationError, Exception) as e:
                        err_msg = str(e)
                        if hasattr(e, "errors"):
                            errs = e.errors()
                            err_msg = "; ".join(
                                f"{'.'.join(str(p) for p in er['loc'])}: {er['msg']}"
                                for er in errs[:3]
                            )
                        error_log.append({
                            "row": abs_row,
                            "field": "schema",
                            "error": f"Validation: {err_msg}",
                            "suggested_fix": "Check field formats and required fields.",
                            "original_value": "",
                        })
                        chunk_failed += 1
                        continue

                    # ── Layer 3: DB business validation ──────────────────────────
                    try:
                        existing = await emp_repo.get_by_email(item.email)

                        if dry_run:
                            # In dry run: only validate, never write
                            if existing:
                                if duplicate_strategy == "fail":
                                    error_log.append({
                                        "row": abs_row,
                                        "field": "email",
                                        "error": f"Duplicate email (dry run): {item.email}",
                                        "suggested_fix": "Change duplicate_strategy or use a different email.",
                                        "original_value": item.email,
                                    })
                                    chunk_failed += 1
                                else:
                                    chunk_skipped += 1
                            else:
                                chunk_succeeded += 1
                            continue

                        # ── Real write ────────────────────────────────────────────
                        emp_create = item.to_employee_create(user_id_override=None)

                        if existing:
                            if duplicate_strategy == "skip":
                                chunk_skipped += 1
                                continue
                            elif duplicate_strategy == "fail":
                                error_log.append({
                                    "row": abs_row,
                                    "field": "email",
                                    "error": f"Duplicate email rejected: {item.email}",
                                    "suggested_fix": "Remove duplicate or change strategy to 'update'.",
                                    "original_value": item.email,
                                })
                                chunk_failed += 1
                                continue
                            else:  # update
                                update_fields = {
                                    k: v
                                    for k, v in emp_create.model_dump(exclude_unset=False).items()
                                    if k not in ("user_id", "account_status", "invite_expires_at", "email")
                                    and v is not None
                                }
                                await _update_employee(db, existing, update_fields, job_uuid)
                                chunk_succeeded += 1
                        else:
                            emp = _build_employee(emp_create, company_uuid, job_uuid)
                            db.add(emp)
                            chunk_succeeded += 1

                    except Exception as e:
                        logger.warning(f"Bulk import row {abs_row} failed: {e}")
                        error_log.append({
                            "row": abs_row,
                            "field": "db",
                            "error": str(e),
                            "suggested_fix": "Check for constraint violations.",
                            "original_value": "",
                        })
                        chunk_failed += 1
                        await db.rollback()
                        continue

                # Commit the whole chunk in one transaction (unless dry run)
                if not dry_run:
                    try:
                        await db.commit()
                    except Exception as commit_err:
                        logger.error(f"Chunk commit failed at start={chunk_start}: {commit_err}")
                        # Mark all rows in this chunk as failed
                        chunk_failed += chunk_succeeded
                        chunk_succeeded = 0
                        error_log.append({
                            "row": chunk_start,
                            "field": "db",
                            "error": f"Chunk commit failed: {commit_err}",
                            "suggested_fix": "Check DB constraints for rows in this chunk.",
                            "original_value": "",
                        })

                succeeded += chunk_succeeded
                failed += chunk_failed
                skipped += chunk_skipped

                # Update progress after each chunk so the frontend can poll live updates
                await job_repo.update_progress(
                    job_uuid,
                    succeeded_rows=succeeded,
                    failed_rows=failed,
                    skipped_rows=skipped,
                    status="processing",
                    error_log=error_log,
                )

        # Final status
        final_status = "dry_run" if dry_run else ("completed" if failed == 0 else "completed")
        await job_repo.update_progress(
            job_uuid,
            succeeded_rows=succeeded,
            failed_rows=failed,
            skipped_rows=skipped,
            status=final_status,
            error_log=error_log,
        )

    logger.info(
        f"Import job {job_id} finished: succeeded={succeeded} failed={failed} skipped={skipped} dry_run={dry_run}"
    )


def _build_employee(emp_create: Any, company_uuid: UUID, job_uuid: UUID) -> "Employee":
    from app.models.employee import Employee
    from app.core.constants import AccountStatus

    data = emp_create.model_dump(exclude_unset=False)
    emp = Employee(
        company_id=company_uuid,
        import_job_id=job_uuid,
        account_status=AccountStatus.NOT_REGISTERED.value,
        user_id=None,
        **{k: v for k, v in data.items() if hasattr(Employee, k) and k not in ("company_id",)},
    )
    return emp


async def _update_employee(db: Any, existing: Any, update_fields: dict, job_uuid: UUID) -> None:
    for k, v in update_fields.items():
        if hasattr(existing, k):
            setattr(existing, k, v)
    existing.import_job_id = job_uuid
    db.add(existing)


@celery_app.task(
    bind=True,
    name="app.tasks.import_tasks.process_bulk_import",
    autoretry_for=(Exception,),
    retry_backoff=True,           # 2s, 4s, 8s
    retry_kwargs={"max_retries": 3},
    acks_late=True,               # Don't ack until task finishes (prevents loss on crash)
    reject_on_worker_lost=True,
)
def process_bulk_import(
    self: Task,
    job_id: str,
    rows: list,
    company_id: str,
    dry_run: bool = False,
    duplicate_strategy: str = "update",
) -> dict:
    """
    Celery task: process a bulk employee import job.

    Args:
        job_id: UUID string of the ImportJob record
        rows: list of cleaned row dicts (after sanitizer has run)
        company_id: UUID string for tenant scoping
        dry_run: if True, validate + check DB but write nothing
        duplicate_strategy: "skip" | "update" | "fail"

    Returns dict with job_id, succeeded, failed, skipped.
    """
    try:
        asyncio.run(
            _run_import(
                job_id=job_id,
                rows=rows,
                company_id=company_id,
                dry_run=dry_run,
                duplicate_strategy=duplicate_strategy,
            )
        )
        return {"job_id": job_id, "status": "finished"}
    except Exception as exc:
        logger.error(f"process_bulk_import task error (job={job_id}): {exc}")
        # Mark job as failed in DB before re-raising for Celery retry
        try:
            async def _mark_failed():
                from sqlalchemy.ext.asyncio import AsyncSession
                from app.db.session import AsyncSessionLocal
                from app.repositories.import_job_repository import ImportJobRepository
                async with AsyncSessionLocal() as db:
                    repo = ImportJobRepository(db, UUID(company_id))
                    await repo.update_status(UUID(job_id), "failed", completed=True)
            asyncio.run(_mark_failed())
        except Exception:
            pass
        raise
