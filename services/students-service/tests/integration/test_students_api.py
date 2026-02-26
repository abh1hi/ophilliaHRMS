import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "students-service"


@pytest.mark.asyncio
async def test_create_and_get_student_api(client: AsyncClient):
    # Create student
    student_data = {
        "student_number": "API-STU-001",
        "first_name": "API",
        "last_name": "Test",
        "date_of_birth": "2010-01-01",
        "gender": "other",
        "email": "test@api.com"
    }
    
    response = await client.post("/api/v1/students/", json=student_data)
    assert response.status_code == 201
    created = response.json()
    assert created["student_number"] == "API-STU-001"
    student_id = created["id"]

    # Get student
    get_response = await client.get(f"/api/v1/students/{student_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == student_id


@pytest.mark.asyncio
async def test_create_and_get_class_api(client: AsyncClient):
    # Create class
    class_data = {
        "name": "Geography 101",
        "grade_level": 8,
        "section": "A",
        "academic_year": "2024-2025"
    }

    response = await client.post("/api/v1/classes/", json=class_data)
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "Geography 101"
    class_id = created["id"]

    # Get class
    get_response = await client.get(f"/api/v1/classes/{class_id}")
    assert get_response.status_code == 200
    assert get_response.json()["grade_level"] == 8
