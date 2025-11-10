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
    """
    Create a custom notification or announcement record in MongoDB.

    This is a thin wrapper over `NotificationCRUD.create_notification` that
    standardizes the call signature used across services.

    Args:
        db (AsyncIOMotorDatabase): Motor async database instance.
        description (str): Notification message/body.
        recipient_type (str): Recipient type (e.g., "user", "admin", "all").
        recipient_id (Optional[int]): Optional recipient identifier.
        notif_type (str): Notification channel/type (default: "message").
        attachments (Optional[Dict[str, Any]]): Optional attachments metadata.
        scheduled_at (Optional[datetime]): Optional scheduled send time.
        sender_type (str): Who sent the notification (default: "system").

    Returns:
        dict: Created notification document (raw MongoDB dict) as returned by CRUD.
    """
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
    """
    Create an announcement notification targeted at a recipient group.

    Args:
        db (AsyncIOMotorDatabase): Motor async database instance.
        payload (AnnouncementCreate): Announcement payload including recipient_type and content.
        current_user (Admin): Admin creating the announcement.

    Returns:
        dict: Created announcement document as returned by the CRUD layer.
    """
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
    """
    Fetch notifications relevant to the currently authenticated user or admin.

    Args:
        current_user (User | Admin): Authenticated principal (user or admin).
        db (AsyncIOMotorDatabase): Motor async database instance.

    Returns:
        List[NotificationResponse]: List of notification response DTOs for the principal.
    """
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
    """
    Delete a notification if it belongs to the current principal or the admin has access.

    Args:
        db (AsyncIOMotorDatabase): Motor async database instance.
        payload (NotificationDelete): Payload containing the notification id to delete.
        current_user (User | Admin): Authenticated principal requesting deletion.

    Returns:
        dict: Simple status dict indicating deletion.

    Raises:
        HTTPException: 404 if the notification is not found or access is denied.
    """
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