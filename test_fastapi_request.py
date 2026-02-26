import asyncio
import sys
from httpx import AsyncClient
from uuid import uuid4

# Setup path so importing app works
sys.path.append("c:/Users/abhin/Desktop/ophilliaHRMS/services/employee-service")

from app.main import app
from app.core.security import get_current_user, TokenPayload

async def test_create():
    async def mock_get_current_user():
        return TokenPayload(sub=str(uuid4()), role="employee", email="test@emp.com")
        
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    try:
        async with AsyncClient(app=app, base_url="http://testServer") as ac:
            response = await ac.post("/api/v1/employees", json={
                "first_name": "API",
                "last_name": "Test",
                "email": "test@emp.com",
                "user_id": str(uuid4()),
                "date_joined": "2024-01-01"
            })
            
            print(f"Status Code: {response.status_code}")
            print(f"Response data: {response.json()}")
    except Exception as e:
        import traceback
        print("====== EXCEPTION ======")
        traceback.print_exc()
        
    app.dependency_overrides.clear()
        
if __name__ == "__main__":
    asyncio.run(test_create())
