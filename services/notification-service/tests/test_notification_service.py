import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime
from fastapi import HTTPException

from app.schemas.notification import NotificationLogCreate, PreferenceUpdate
from app.services.notification_service import compile_and_send_notification, get_or_create_preference, update_preference
from app.models.notification import NotificationPreference, NotificationLog
from app.core.constants import NotificationType, NotificationStatus

@pytest.mark.asyncio
async def test_get_or_create_preference_creates_new():
    db_mock = AsyncMock()
    user_id = uuid4()
    
    # Mock no existing pref
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    db_mock.execute.return_value = mock_result
    
    # To simulate db.refresh setting the id
    def mock_add(obj):
        if isinstance(obj, NotificationPreference):
            obj.id = uuid4()
    db_mock.add = MagicMock(side_effect=mock_add)
    
    result = await get_or_create_preference(db_mock, user_id)
    
    assert result.user_id == user_id
    assert result.email_enabled == 1
    assert result.sms_enabled == 1
    db_mock.add.assert_called_once()
    db_mock.commit.assert_called_once()


@pytest.mark.asyncio
async def test_compile_and_send_success():
    db_mock = AsyncMock()
    user_id = uuid4()
    
    # User has email enabled
    mock_pref = NotificationPreference(user_id=user_id, email_enabled=1, sms_enabled=1)
    
    log_in = NotificationLogCreate(
        user_id=user_id,
        type=NotificationType.EMAIL,
        subject="Test Subject",
        message="Test Message"
    )
    
    def mock_add(obj):
        if isinstance(obj, NotificationLog):
            obj.id = uuid4()
    db_mock.add = MagicMock(side_effect=mock_add)
    
    with patch("app.services.notification_service.get_or_create_preference", return_value=mock_pref):
        result = await compile_and_send_notification(db_mock, log_in)
        
        assert result.status == NotificationStatus.SENT.value
        assert result.subject == "Test Subject"
        db_mock.add.assert_called_once()

@pytest.mark.asyncio
async def test_compile_and_send_failed_due_to_preference():
    db_mock = AsyncMock()
    user_id = uuid4()
    
    # User opted out of SMS
    mock_pref = NotificationPreference(user_id=user_id, email_enabled=1, sms_enabled=0)
    
    log_in = NotificationLogCreate(
        user_id=user_id,
        type=NotificationType.SMS,
        message="Test SMS"
    )
    
    def mock_add(obj):
        if isinstance(obj, NotificationLog):
            obj.id = uuid4()
    db_mock.add = MagicMock(side_effect=mock_add)
    
    with patch("app.services.notification_service.get_or_create_preference", return_value=mock_pref):
        result = await compile_and_send_notification(db_mock, log_in)
        
        assert result.status == NotificationStatus.FAILED.value
        assert "disabled" in result.error_message
        db_mock.add.assert_called_once()
