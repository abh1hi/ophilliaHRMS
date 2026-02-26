import sys
import uuid
from datetime import date

# Add the service to the path
sys.path.append("c:/Users/abhin/Desktop/ophilliaHRMS/services/employee-service")

from app.schemas.employee import EmployeeCreate

try:
    EmployeeCreate(
        first_name="API",
        last_name="Test",
        email="test@emp.com",
        user_id=uuid.uuid4(),
        date_joined=date(2024, 1, 1)
    )
    print("Validation successful!")
except Exception as e:
    print("====== ERROR DETECTED ======")
    print(e)
