# crud/notification.py
from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import pymongo
from ..schemas.notification import RecipientType, AnnouncementRecipientType, PyObjectId

class NotificationCRUD:
    COLLECTION = "notifications"

    @staticmethod
    async def create_notification(
        db: AsyncIOMotorDatabase,
        sender_type: str,
        description: str,
        recipient_type: str,
        recipient_id: Optional[int],
        notif_type: str,
        attachments: Optional[Dict[str, Any]] = None,
        scheduled_at: Optional[datetime] = None
    ) -> dict:
        """
        Create a new notification in MongoDB.

        Args:
            db (AsyncIOMotorDatabase): Motor async database instance.
            sender_type (str): Type of sender (e.g., 'admin', 'system').
            description (str): Notification message.
            recipient_type (str): Type of recipient (e.g., 'all_users', 'admin', 'user').
            recipient_id (Optional[int]): ID of specific recipient if applicable.
            notif_type (str): Type of notification (e.g., 'announcement', 'alert').
            attachments (Optional[Dict[str, Any]]): Optional attachment data.
            scheduled_at (Optional[datetime]): Scheduled delivery time.

        Returns:
            dict: The created notification document.
        """
        notification_doc = {
            "sender_type": sender_type,
            "description": description,
            "recipient_type": recipient_type,
            "recipient_id": recipient_id,
            "status": "delivered",
            "type": notif_type,
            "attachments": attachments or {},
            "created_at": datetime.now(),
            "scheduled_at": scheduled_at
        }

        res = await db[NotificationCRUD.COLLECTION].insert_one(notification_doc)
        return notification_doc

    @staticmethod
    async def get_user_notifications(
        db: AsyncIOMotorDatabase,
        user_id: Optional[int] = None,
        admin_id: Optional[int] = None,
    ) -> List[Dict]:
        """
        Retrieve notifications for a user or admin based on recipient criteria.

        Fetches notifications that match the user/admin ID or recipient type (all_users, prepaid_users, etc.).

        Args:
            db (AsyncIOMotorDatabase): Motor async database instance.
            user_id (Optional[int]): ID of the user retrieving notifications.
            admin_id (Optional[int]): ID of the admin retrieving notifications.

        Returns:
            List[Dict]: List of notifications sorted by creation date descending.
        """
        query = {"$or": []}
        
        if admin_id is not None:
            admin_query = [
                {"recipient_type": "all_admin"},
                {"recipient_type": "all_users"},
                {"recipient_type": "prepaid_users"},
                {"recipient_type": "postpaid_users"},
                {"recipient_id": admin_id}
            ]
            query["$or"].extend(admin_query)
        elif user_id is not None:
            user_query = [
                {"recipient_type": "all_user"},
                {"recipient_type": "prepaid_users"},
                {"recipient_type": "postpaid_users"},
                {"recipient_id": user_id}
            ]
            query["$or"].extend(user_query)

        if not query["$or"]:
            return []

        cursor = db[NotificationCRUD.COLLECTION].find(query).sort("created_at", pymongo.DESCENDING)
        notifications = await cursor.to_list()
        return notifications

    @staticmethod
    async def delete_notification(db: AsyncIOMotorDatabase, _id: PyObjectId, user_id: Optional[int], admin_id: Optional[int]) -> bool:
        """
        Delete a notification if the user/admin has permission.

        Broadcast notifications (all_users, prepaid_users, etc.) cannot be deleted.
        Personal notifications can only be deleted by their intended recipient.

        Args:
            db (AsyncIOMotorDatabase): Motor async database instance.
            _id (PyObjectId): MongoDB ObjectId of the notification.
            user_id (Optional[int]): ID of the user attempting deletion.
            admin_id (Optional[int]): ID of the admin attempting deletion.

        Returns:
            bool: True if notification was deleted, False otherwise.
        """
        notification = await db[NotificationCRUD.COLLECTION].find_one({"_id": ObjectId(_id)})
        if not notification:
            return False

        recip_type = notification["recipient_type"]
        recip_id = notification["recipient_id"]

        if recip_type in ["all_users", "prepaid_users", "postpaid_users", "blocked", "all_admin"]:
            return False
        if recip_type == "admin" and admin_id is None:
            return False
        if recip_type == "user" and user_id is None:
            return False
        if recip_id is not None and recip_id != (user_id or admin_id):
            return False

        result = await db[NotificationCRUD.COLLECTION].delete_one({"_id": ObjectId(_id)})
        return result.deleted_count > 0

    @staticmethod
    async def create_announcement(
        db: AsyncIOMotorDatabase,
        recipient_type: AnnouncementRecipientType,
        description: str,
        attachments: Optional[Dict[str, Any]] = None,
        scheduled_at: Optional[datetime] = None
    ) -> dict:
        """
        Create an announcement notification for specified recipients.

        Args:
            db (AsyncIOMotorDatabase): Motor async database instance.
            recipient_type (AnnouncementRecipientType): Recipient type enum value.
            description (str): Announcement message.
            attachments (Optional[Dict[str, Any]]): Optional attachment data.
            scheduled_at (Optional[datetime]): Scheduled delivery time.

        Returns:
            dict: The created announcement notification document.
        """
        return await NotificationCRUD.create_notification(
            db=db,
            sender_type="admin",
            description=description,
            recipient_type=recipient_type.value,
            recipient_id=None,
            notif_type="announcement",
            attachments=attachments,
            scheduled_at=scheduled_at
        )