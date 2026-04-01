# Import all models so SQLAlchemy & Alembic can discover them
from app.models.attendance_record import AttendanceRecord  # noqa: F401
from app.models.attendance_task import AttendanceTask  # noqa: F401
from app.models.attendance_policy import AttendancePolicy  # noqa: F401
from app.models.geofence_location import GeofenceLocation  # noqa: F401
from app.models.task_template import TaskTemplate  # noqa: F401
from app.models.idempotency_key import IdempotencyKey  # noqa: F401
from app.models.policy_audit_log import PolicyAuditLog  # noqa: F401
from app.models.policy_template import PolicyTemplate  # noqa: F401
from app.models.policy_exception import PolicyException  # noqa: F401
