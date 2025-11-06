# services/notification.py
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models.admins import Admin
from ..models.users import User
from ..schemas.notification import (
    NotificationCreate, NotificationResponse, AnnouncementCreate,
    NotificationMarkViewed, NotificationDelete
)
from ..crud.notification import NotificationCRUD
from ..dependencies.auth import get_current_user  # assuming this returns user with user_id/admin_id

async def create_custom_notification(
    db: AsyncIOMotorDatabase,
    description: str,
    recipient_type: str,
    recipient_id: Optional[int] = None,
    notif_type: str = "message",
    attachments: Optional[Dict[str, Any]] = None,
    scheduled_at: Optional[datetime] = None,
    sender_type: str = "system"
) -> dict:
    """Utility function to create any notification"""
    return await NotificationCRUD.create_notification(
        db=db,
        sender_type=sender_type,
        description=description,
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        notif_type=notif_type,
        attachments=attachments,
        scheduled_at=scheduled_at
    )

async def service_create_announcement(
    db: AsyncIOMotorDatabase,
    payload: AnnouncementCreate,
    current_user: Admin
) -> dict:    
    notif_dict = await NotificationCRUD.create_announcement(
        db=db,
        recipient_type=payload.recipient_type,
        description=payload.description,
        attachments=payload.attachments,
        scheduled_at=payload.scheduled_at
    )
    return notif_dict

async def service_get_my_notifications(
    current_user: User | Admin,
    db: AsyncIOMotorDatabase,
):
    if isinstance(current_user, User):
        notifications = await NotificationCRUD.get_user_notifications(
            db=db,
            user_id=current_user.user_id,
            admin_id=None,
        )
    else:
        notifications = await NotificationCRUD.get_user_notifications(
            db=db,
            user_id=None,
            admin_id=current_user.admin_id,
        )
    return [NotificationResponse(**n) for n in notifications]

async def service_delete_notification(
    db: AsyncIOMotorDatabase,
    payload: NotificationDelete,
    current_user: User | Admin,
):  
    if isinstance(current_user, User):
        success = await NotificationCRUD.delete_notification(
            db=db,
            _id=payload.id,
            user_id=current_user.user_id,
            admin_id=None
        )
    else:
        success = await NotificationCRUD.delete_notification(
            db=db,
            _id=payload.id,
            user_id=None,
            admin_id=current_user.admin_id
        )
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found or access denied")
    return {"status": "deleted"}