from fastapi import APIRouter, Depends, Query, Security
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List

from ....models.users import User
from ....models.admins import Admin
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes
from ....schemas.notification import (
    AnnouncementCreate, NotificationResponse,
    NotificationMarkViewed, NotificationDelete
)
from ....services.notification import (
    service_create_announcement,
    service_get_my_notifications,
    service_delete_notification
)
from ....core.document_db import get_mongo_db as get_db  # your DB dependency

router = APIRouter()

@router.post("/announcement", status_code=201, response_model=NotificationResponse)
async def create_announcement(
    payload: AnnouncementCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Announcement:write"])
):
    """
    Create a new announcement for system users.
    
    Allows admins to create and broadcast system-wide announcements to all users
    or targeted user segments. Announcements are pushed to users' notification
    centers and can include important updates, promotions, maintenance notices,
    or urgent information requiring user attention.
    
    Security:
        - Requires valid JWT access token
        - Scope: Announcement:write
        - Only admins can create announcements
        - Broadcasts are logged for audit purposes
    
    Request Body:
        AnnouncementCreate (JSON):
            - title (str): Announcement title (max 200 chars, required)
            - message (str): Announcement content (max 5000 chars, required)
            - type (str): Announcement type (info, warning, promotion, maintenance)
            - target_users (list, optional): User IDs to target (all if not provided)
            - target_segment (str, optional): Segment criteria (prepaid, postpaid, all)
            - priority (int, optional): Display priority level (1=low, 5=critical)
            - expires_at (datetime, optional): When announcement expires
            - action_url (str, optional): Deep link URL for action button
    
    Returns:
        NotificationResponse:
            - notification_id (str): Unique identifier
            - title (str): Announcement title
            - message (str): Announcement content
            - type (str): Announcement type
            - created_by (int): Admin ID who created it
            - created_at (datetime): Creation timestamp
            - expires_at (datetime): Expiration time if applicable
            - priority (int): Priority level
    
    Raises:
        HTTPException(400): Invalid announcement data or validation error
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Announcement:write scope
        HTTPException(422): Invalid target users or segments
    
    Example:
        Request:
            POST /notification/announcement
            Headers: Authorization: Bearer <jwt_token>
            Body:
            {
                "title": "Special Year-End Offer",
                "message": "Get 50% discount on all plans this week!",
                "type": "promotion",
                "target_segment": "prepaid",
                "priority": 3,
                "action_url": "/offers/yearend"
            }
        
        Response (201 Created):
            {
                "notification_id": "ann_12345",
                "title": "Special Year-End Offer",
                "message": "Get 50% discount on all plans this week!",
                "type": "promotion",
                "created_by": 1,
                "created_at": "2024-01-20T10:00:00Z",
                "priority": 3
            }
    """
    return await service_create_announcement(db, payload, current_user)


@router.get("/my", response_model=List[NotificationResponse])
async def get_my_notifications(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Admin | User = Depends(get_current_user),
    # no ned of scopes cause any admin or user can get their noti
):
    """
    Retrieve all notifications for the current user.
    
    Fetches all notifications belonging to the current user including
    system announcements, transaction receipts, plan reminders, promotional
    offers, and administrative messages. Ordered by most recent first.
    
    Security:
        - Requires valid JWT access token
        - No specific scope required
        - Users can only view their own notifications
        - Admins can only view their own notifications
    
    Returns:
        List[NotificationResponse]: Array of notification objects:
            - notification_id (str): Unique identifier
            - title (str): Notification title
            - message (str): Notification content
            - type (str): Notification type (announcement, transaction, reminder, etc.)
            - is_read (bool): Whether user has read this notification
            - created_at (datetime): When notification was sent
            - read_at (datetime, optional): When user read it
            - action_url (str, optional): Deep link for action button
            - priority (int): Priority level for display order
            - data (dict, optional): Additional metadata/context
    
    Raises:
        HTTPException(401): User not authenticated
    
    Example:
        Request:
            GET /notification/my
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            [
                {
                    "notification_id": "notif_67890",
                    "title": "Plan Renewal Reminder",
                    "message": "Your plan expires tomorrow. Renew now to continue service.",
                    "type": "reminder",
                    "is_read": false,
                    "created_at": "2024-01-20T09:00:00Z",
                    "priority": 4,
                    "action_url": "/recharge/plans"
                },
                {
                    "notification_id": "ann_12345",
                    "title": "Special Year-End Offer",
                    "message": "Get 50% discount on all plans this week!",
                    "type": "announcement",
                    "is_read": true,
                    "created_at": "2024-01-19T14:00:00Z",
                    "read_at": "2024-01-19T14:15:00Z",
                    "priority": 3,
                    "action_url": "/offers/yearend"
                }
            ]
    """
    return await service_get_my_notifications(db=db, current_user=current_user)
    

@router.delete("/delete")
async def delete_notification(
    payload: NotificationDelete,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User | Admin = Depends(get_current_user),
    # no need of scopes cause any admin or user can delete their noti
):
    """
    Delete a notification from the current user's inbox.
    
    Removes a notification from user's notification center. This action is
    permanent and the notification cannot be recovered. Useful for users to
    clean up their notification history and declutter their inbox.
    
    Security:
        - Requires valid JWT access token
        - No specific scope required
        - Users can only delete their own notifications
        - Admins can only delete their own notifications
    
    Request Body:
        NotificationDelete (JSON):
            - notification_id (str): ID of notification to delete (required)
    
    Returns:
        dict: Deletion confirmation:
            {
                "message": "Notification deleted successfully",
                "notification_id": <str>,
                "deleted_at": <datetime>
            }
    
    Raises:
        HTTPException(400): Invalid notification ID format
        HTTPException(401): User not authenticated
        HTTPException(404): Notification not found or doesn't belong to user
        HTTPException(500): Database deletion error
    
    Example:
        Request:
            DELETE /notification/delete
            Headers: Authorization: Bearer <jwt_token>
            Body:
            {
                "notification_id": "notif_67890"
            }
        
        Response (200 OK):
            {
                "message": "Notification deleted successfully",
                "notification_id": "notif_67890",
                "deleted_at": "2024-01-20T10:30:00Z"
            }
    """
    return await service_delete_notification(db=db, current_user=current_user, payload=payload)