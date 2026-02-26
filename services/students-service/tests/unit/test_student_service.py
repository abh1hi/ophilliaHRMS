import pytest
from datetime import date
import uuid

from app.models.student import GenderEnum, StudentStatusEnum
from app.schemas.student import StudentCreate
from app.services.student_service import StudentService
from app.events.publisher import EventPublisher

class MockEventPublisher(EventPublisher):
    def __init__(self):
        self.published_events = []

    async def connect(self):
        pass

    async def close(self):
        pass

    async def publish(self, event_type: str, payload: dict, routing_key: str = None):
        self.published_events.append({"type": event_type, "payload": payload})


@pytest.mark.asyncio
async def test_create_student_success(db_session):
    publisher = MockEventPublisher()
    service = StudentService(db_session, publisher)

    student_data = StudentCreate(
        student_number="STU-001",
        first_name="John",
        last_name="Doe",
        date_of_birth=date(2010, 5, 15),
        gender=GenderEnum.male,
        email="john.doe@example.com"
    )

    student = await service.create_student(student_data)

    assert student.id is not None
    assert student.student_number == "STU-001"
    assert student.first_name == "John"
    
    # Verify event published
    assert len(publisher.published_events) == 1
    event = publisher.published_events[0]
    assert event["type"] == "student.enrolled"
    assert event["payload"]["student_number"] == "STU-001"


@pytest.mark.asyncio
async def test_create_student_duplicate_number(db_session):
    publisher = MockEventPublisher()
    service = StudentService(db_session, publisher)

    student_data = StudentCreate(
        student_number="STU-002",
        first_name="Jane",
        last_name="Doe",
        date_of_birth=date(2011, 6, 20),
        gender=GenderEnum.female
    )

    await service.create_student(student_data)

    # Attempt to create duplicate
    with pytest.raises(Exception) as excinfo:
        await service.create_student(student_data)
        
    assert "already exists" in str(excinfo.value)


@pytest.mark.asyncio
async def test_change_student_status(db_session):
    publisher = MockEventPublisher()
    service = StudentService(db_session, publisher)

    student_data = StudentCreate(
        student_number="STU-003",
        first_name="Alice",
        last_name="Smith",
        date_of_birth=date(2009, 1, 1),
        gender=GenderEnum.female
    )

    student = await service.create_student(student_data)
    publisher.published_events.clear() # Clear enroll event

    updated_student = await service.change_status(student.id, StudentStatusEnum.graduated)

    assert updated_student.status == StudentStatusEnum.graduated
    
    # Verify event published
    assert len(publisher.published_events) == 2
    assert publisher.published_events[0]["type"] == "student.status_changed"
    assert publisher.published_events[1]["type"] == "student.graduated"
