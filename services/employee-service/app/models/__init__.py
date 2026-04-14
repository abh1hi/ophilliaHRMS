# Import all models here so SQLAlchemy's mapper registry has every class
# registered before any relationship string-references are resolved.
# This is critical for Celery workers which don't boot via the FastAPI app.
from app.models.department import Department
from app.models.branch import Branch
from app.models.designation import Designation
from app.models.employee_grade import EmployeeGrade
from app.models.employee_group import EmployeeGroup
from app.models.employment_type import EmploymentType
from app.models.shift_type import ShiftType
from app.models.shift_location import ShiftLocation
from app.models.import_job import ImportJob
from app.models.employee import Employee  # last — depends on all of the above

__all__ = [
    "Department",
    "Branch",
    "Designation",
    "EmployeeGrade",
    "EmployeeGroup",
    "EmploymentType",
    "ShiftType",
    "ShiftLocation",
    "ImportJob",
    "Employee",
]
