"""Cross-service employee validation — verifies employee belongs to current tenant."""
import logging
from uuid import UUID
from fastapi import HTTPException, status
from app.core.http_client import get_http_client
from app.core.config import settings

logger = logging.getLogger(__name__)


async def validate_employee_tenant(employee_id: UUID, expected_company_id: str) -> None:
    """Verify that employee_id belongs to expected_company_id via employee-service lookup.

    Raises HTTPException 404 if employee not found or belongs to different company.
    Fails open (logs warning, allows request) if employee-service is unreachable.
    """
    try:
        async with get_http_client() as client:
            resp = await client.get(
                f"{settings.EMPLOYEE_SERVICE_URL}/api/v1/employees/internal/{employee_id}"
            )
            if resp.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Employee {employee_id} not found",
                )
            if resp.status_code == 200:
                data = resp.json()
                emp_company = data.get("company_id")
                if emp_company and str(emp_company) != str(expected_company_id):
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Employee {employee_id} not found",
                    )
            # Non-200/404 responses: log warning, allow request (fail-open)
            elif resp.status_code != 200:
                logger.warning(
                    f"Employee validation returned {resp.status_code} — allowing request",
                    extra={"employee_id": str(employee_id)},
                )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(
            f"Employee service unreachable for validation — allowing request: {exc}",
            extra={"employee_id": str(employee_id)},
        )
