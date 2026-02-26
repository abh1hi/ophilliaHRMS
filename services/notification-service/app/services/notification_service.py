import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.notification import NotificationPreference, NotificationLog
from app.schemas.notification import NotificationLogCreate, PreferenceCreate, PreferenceUpdate
from app.core.constants import NotificationStatus

logger = logging.getLogger(__name__)

async def get_or_create_preference(db: AsyncSession, user_id: UUID) -> NotificationPreference:
    result = await db.execute(select(NotificationPreference).filter(NotificationPreference.user_id == user_id))
    pref = result.scalars().first()
    
    if not pref:
        pref = NotificationPreference(user_id=user_id, email_enabled=1, sms_enabled=1)
        db.add(pref)
        await db.commit()
        await db.refresh(pref)
        
    return pref

async def update_preference(db: AsyncSession, user_id: UUID, pref_update: PreferenceUpdate) -> NotificationPreference:
    pref = await get_or_create_preference(db, user_id)
    
    pref.email_enabled = 1 if pref_update.email_enabled else 0
    pref.sms_enabled = 1 if pref_update.sms_enabled else 0
    
    db.add(pref)
    await db.commit()
    await db.refresh(pref)
    
    return pref

async def compile_and_send_notification(db: AsyncSession, log_create: NotificationLogCreate):
    """
    Simulates sending an Email/SMS by checking preferences and saving a log.
    If the format is EMAIL, and the user hasn't opted out of email, it succeeds.
    """
    pref = await get_or_create_preference(db, log_create.user_id)
    
    # Check bounds
    should_send = False
    if log_create.type == "EMAIL" and pref.email_enabled:
        should_send = True
    elif log_create.type == "SMS" and pref.sms_enabled:
        should_send = True
        
    if should_send:
        logger.info(f"Simulating sending {log_create.type} to {log_create.user_id}: {log_create.subject}")
        # In a real environment, you trigger SendGrid, Twilio, etc.
        # Once it succeeds:
        log_create.status = NotificationStatus.SENT
    else:
        logger.info(f"User {log_create.user_id} opted out of {log_create.type} notifications.")
        log_create.status = NotificationStatus.FAILED
        log_create.error_message = f"User has disabled {log_create.type} notifications"
        
    db_obj = NotificationLog(**log_create.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

