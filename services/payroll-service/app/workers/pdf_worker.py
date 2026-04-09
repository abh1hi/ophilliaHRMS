"""PDF Worker — Async payslip PDF generation.

Runs as background task after payroll processing completes.
Subscribes to payroll.payslips_ready event and generates PDFs.
"""
import asyncio
import base64
import logging
from uuid import UUID
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.services.pdf_service import PDFService
from app.repositories.payroll_repository import PayrollRepository

logger = logging.getLogger(__name__)


class PDFWorker:
    """Background worker for generating payslip PDFs."""

    def __init__(self, database_url: str):
        """Initialize PDF worker with database connection.

        Args:
            database_url: Async database URL
        """
        self.engine = create_async_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.pdf_service = PDFService()

    async def generate_payslips_for_run(
        self,
        payroll_run_id: UUID,
        company_id: UUID,
    ) -> Dict[str, Any]:
        """Generate PDFs for all payslips in a payroll run.

        Called when payroll transitions to COMPLETED state.

        Args:
            payroll_run_id: PayrollRun UUID
            company_id: Company UUID

        Returns:
            Dict with generation results: {success: int, failed: int, errors: []}
        """
        async with self.SessionLocal() as db:
            # Set company_id on session for tenant isolation
            db.info["company_id"] = str(company_id)

            repo = PayrollRepository(db)
            run = await repo.get_payroll_run(payroll_run_id)

            if not run:
                logger.error(f"PayrollRun {payroll_run_id} not found")
                return {"success": 0, "failed": 0, "errors": ["PayrollRun not found"]}

            payslips = await repo.get_payslips_by_run(payroll_run_id)

            success_count = 0
            failed_count = 0
            errors = []

            logger.info(
                f"Starting PDF generation for {len(payslips)} payslips",
                extra={"run_id": str(payroll_run_id), "count": len(payslips)},
            )

            for payslip in payslips:
                try:
                    # Generate PDF for this payslip
                    pdf_bytes = await self._generate_single_payslip_pdf(
                        payslip, run, company_id, db
                    )

                    # Store PDF as base64 in database
                    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
                    payslip.pdf_data = pdf_base64

                    success_count += 1

                    logger.info(
                        f"Payslip PDF generated: {payslip.employee_id}",
                        extra={"employee_id": str(payslip.employee_id)},
                    )

                except Exception as e:
                    failed_count += 1
                    error_msg = f"PDF generation failed for {payslip.employee_id}: {str(e)}"
                    errors.append(error_msg)
                    logger.exception(
                        f"Payslip PDF generation error",
                        extra={"employee_id": str(payslip.employee_id)},
                    )

            # Commit all PDF changes
            try:
                await db.commit()
                logger.info(
                    f"PDF generation completed: {success_count} success, {failed_count} failed",
                    extra={
                        "run_id": str(payroll_run_id),
                        "success": success_count,
                        "failed": failed_count,
                    },
                )
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to commit PDF data: {str(e)}")
                return {
                    "success": 0,
                    "failed": len(payslips),
                    "errors": [f"Database commit failed: {str(e)}"],
                }

            # Publish notification event (fire-and-forget)
            # TODO: Integrate with event publisher
            # await event_publisher.publish("payroll.payslips_ready", {
            #     "run_id": str(payroll_run_id),
            #     "success": success_count,
            #     "failed": failed_count,
            # })

            return {
                "success": success_count,
                "failed": failed_count,
                "errors": errors,
            }

    async def _generate_single_payslip_pdf(
        self,
        payslip,
        payroll_run,
        company_id: UUID,
        db: AsyncSession,
    ) -> bytes:
        """Generate PDF for a single payslip.

        Args:
            payslip: Payslip model instance
            payroll_run: PayrollRun model instance
            company_id: Company UUID
            db: Database session

        Returns:
            PDF file as bytes
        """
        repo = PayrollRepository(db)

        # TODO: Fetch actual employee data from employee service
        employee_data = {
            "id": payslip.employee_id,
            "name": f"Employee {payslip.employee_id}",
            "designation": "Staff",
            "department": "Operations",
            "joining_date": None,
            "uan": "UAN123456",
            "bank_account_masked": "XXXX****XXXX",
            "salary_structure": "Standard",
            "cost_center": "CC001",
        }

        # TODO: Fetch actual company data
        company_data = {
            "name": "OphilliaHRMS",
            "address": "Company Address, City, State",
            "phone": "+91-XXXXXXXXXX",
            "email": "hr@company.com",
        }

        # Get YTD data for the financial year
        fy = payroll_run.period_start.year if payroll_run.period_start.month >= 4 else payroll_run.period_start.year - 1
        ytd = await repo.get_employee_ytd(payslip.employee_id, fy)

        ytd_data = {
            "ytd_gross": ytd.ytd_gross if ytd else 0,
            "ytd_basic": ytd.ytd_basic if ytd else 0,
            "ytd_pf_employee": ytd.ytd_pf_employee if ytd else 0,
            "ytd_esi_employee": ytd.ytd_esi_employee if ytd else 0,
            "ytd_professional_tax": ytd.ytd_professional_tax if ytd else 0,
            "ytd_tds": ytd.ytd_tds if ytd else 0,
        }

        # Build payslip data dict from model
        payslip_data = {
            "gross": payslip.gross,
            "net": payslip.net,
            "ctc": payslip.ctc,
            "basic": payslip.basic,
            "hra": payslip.hra,
            "allowances": payslip.allowances,
            "pf_deduction": payslip.pf_deduction,
            "esi_deduction": payslip.esi_deduction,
            "professional_tax": payslip.professional_tax,
            "tds_deduction": payslip.tds_deduction,
            "lwf_employee": payslip.lwf_employee,
            "total_deductions": payslip.total_deductions,
            "period_start": payslip.period_start,
            "period_end": payslip.period_end,
            "pro_rata_factor": payslip.pro_rata_factor,
            "lop_days": payslip.lop_days,
            "lop_amount": payslip.lop_amount,
            "effective_from": None,  # TODO: Fetch from employee_salary
        }

        # Generate PDF
        pdf_bytes = await self.pdf_service.generate_payslip_pdf(
            payslip_data, company_data, employee_data, ytd_data
        )

        return pdf_bytes


async def run_pdf_worker():
    """Main entry point for PDF worker (runs as background service)."""
    logger.info("PDF Worker started")

    worker = PDFWorker(settings.DATABASE_URL)

    try:
        # Listen for payroll.payslips_ready events
        # In production, this would subscribe to RabbitMQ/event bus
        # For now, this is a placeholder
        while True:
            # TODO: Implement event subscription
            # event = await event_queue.get()
            # if event.type == "payroll.payslips_ready":
            #     await worker.generate_payslips_for_run(
            #         event.run_id,
            #         event.company_id
            #     )
            await asyncio.sleep(10)

    except Exception as e:
        logger.exception(f"PDF Worker error: {str(e)}")
    finally:
        await worker.engine.dispose()
        logger.info("PDF Worker stopped")


if __name__ == "__main__":
    asyncio.run(run_pdf_worker())
