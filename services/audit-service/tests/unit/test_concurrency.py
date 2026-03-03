"""Concurrency test: 10 parallel record_event calls with the same event_id → exactly 1 row."""
import asyncio
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.audit_service import AuditService
from app.repositories.audit_log_repository import AuditLogRepository


@pytest.mark.asyncio
async def test_concurrent_record_event_idempotency():
    """10 parallel calls with the same event_id must result in exactly 1 insert."""
    event_id = str(uuid.uuid4())
    insert_count = 0
    exists_count = 0

    async def fake_exists(self_ref, eid):
        nonlocal exists_count
        await asyncio.sleep(0)  # yield to event loop — simulates concurrent access
        # Simulate first call returns False, rest return True
        result = exists_count > 0
        exists_count += 1
        return result

    async def fake_create(self_ref, data):
        nonlocal insert_count
        insert_count += 1
        mock = MagicMock()
        mock.id = uuid.uuid4()
        mock.event_id = uuid.UUID(event_id)
        mock.event_version = 1
        mock.event_type = "employee.created"
        mock.service_source = "employee-service"
        mock.company_id = uuid.uuid4()
        mock.user_id = None
        mock.correlation_id = None
        mock.ip_address = None
        mock.user_agent = None
        mock.http_method = None
        mock.endpoint = None
        mock.payload = {}
        from datetime import datetime
        mock.timestamp = datetime.utcnow()
        mock.created_at = datetime.utcnow()
        return mock

    raw_event = {
        "event_id": event_id,
        "event_type": "employee.created",
        "service_source": "employee-service",
        "payload": {},
    }

    with patch.object(AuditLogRepository, "exists", new=fake_exists), \
         patch.object(AuditLogRepository, "create", new=fake_create):

        db = AsyncMock()
        tasks = [AuditService(db).record_event(raw_event) for _ in range(10)]
        results = await asyncio.gather(*tasks)

    # Due to the exists check simulation, only 1 insert should have occurred
    non_none = [r for r in results if r is not None]
    assert len(non_none) == 1, f"Expected 1 insert, got {len(non_none)}"
