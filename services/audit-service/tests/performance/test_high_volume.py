"""High-volume insert test: mock 10k events and verify no memory spike."""
import asyncio
import gc
import tracemalloc
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.audit_service import AuditService
from app.repositories.audit_log_repository import AuditLogRepository


def make_mock_log(event_id_str: str):
    mock = MagicMock()
    mock.id = uuid.uuid4()
    mock.event_id = uuid.UUID(event_id_str)
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
    mock.timestamp = datetime.utcnow()
    mock.created_at = datetime.utcnow()
    return mock


@pytest.mark.asyncio
async def test_high_volume_10k_events():
    """10k unique events should all be processed without a significant memory spike."""
    events = [
        {
            "event_id": str(uuid.uuid4()),
            "event_type": "employee.created",
            "service_source": "employee-service",
            "payload": {"name": f"Employee {i}"},
        }
        for i in range(10_000)
    ]

    async def fake_exists(self_ref, event_id):
        return False

    async def fake_create(self_ref, data):
        return make_mock_log(str(data["event_id"]))

    tracemalloc.start()
    gc.collect()
    snapshot_before = tracemalloc.take_snapshot()

    with patch.object(AuditLogRepository, "exists", new=fake_exists), \
         patch.object(AuditLogRepository, "create", new=fake_create):
        db = AsyncMock()

        # Process in batches of 100 to avoid overly deep event loops
        batch_size = 100
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            tasks = [AuditService(db).record_event(e) for e in batch]
            results = await asyncio.gather(*tasks)
            assert all(r is not None for r in results)

    gc.collect()
    snapshot_after = tracemalloc.take_snapshot()
    tracemalloc.stop()

    # Calculate memory delta in MB
    stats = snapshot_after.compare_to(snapshot_before, "lineno")
    total_diff_mb = sum(s.size_diff for s in stats) / (1024 * 1024)

    # Allow max 100MB for 10k events — should be well under this
    assert total_diff_mb < 100, (
        f"Memory spike detected: {total_diff_mb:.2f}MB for 10k events"
    )
