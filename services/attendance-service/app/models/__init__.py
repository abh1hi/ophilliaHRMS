# Import all models so SQLAlchemy & Alembic can discover them
from app.models.attendance_record import AttendanceRecord  # noqa: F401
from app.models.attendance_task import AttendanceTask  # noqa: F401
from app.models.attendance_policy import AttendancePolicy  # noqa: F401
from app.models.geofence_location import GeofenceLocation  # noqa: F401
