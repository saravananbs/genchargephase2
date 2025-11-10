# schemas/notification.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, GetJsonSchemaHandler
from datetime import datetime
from enum import Enum
from typing import Literal
from pydantic_core import core_schema
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom Pydantic type for MongoDB ObjectId serialization.
    
    Enables proper JSON serialization of MongoDB ObjectIds as strings while maintaining
    type safety in Pydantic models.
    """
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetJsonSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.is_instance_schema(ObjectId),
            serialization=core_schema.plain_serializer_function_ser_schema(lambda oid: str(oid)),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler) -> dict:
        json_schema = handler(core_schema)
        json_schema.update(type="string", format="objectid", example="507f1f77bcf86cd799439011")
        return json_schema


class SenderType(str, Enum):
    """Enumeration for notification sender types.
    
    Attributes:
        system (str): Notification from system/application.
        admin (str): Notification from admin user.
    """
    system = "system"
    admin = "admin"

class AnnouncementRecipientType(str, Enum):
    """Enumeration for announcement recipient types.
    
    Attributes:
        all_admin (str): All admin users.
        all_users (str): All regular users.
        prepaid_users (str): Users with prepaid plans.
        postpaid_users (str): Users with postpaid plans.
        blocked (str): Blocked/inactive users.
    """
    all_admin = "all_admin"
    all_users = "all_users"
    prepaid_users = "prepaid_users"
    postpaid_users = "postpaid_users"
    blocked = "blocked"

class RecipientType(str, Enum):
    """Enumeration for notification recipient types.
    
    Attributes:
        admin (str): Specific admin user.
        all_admin (str): All admin users.
        user (str): Specific regular user.
        all_users (str): All regular users.
        prepaid_users (str): Users with prepaid plans.
        postpaid_users (str): Users with postpaid plans.
        blocked (str): Blocked/inactive users.
    """
    admin = "admin"
    all_admin = "all_admin"
    user = "user"
    all_users = "all_user"
    prepaid_users = "prepaid_users"
    postpaid_users = "postpaid_users"
    blocked = "blocked"

class NotificationStatus(str, Enum):
    """Enumeration for notification delivery/viewing status.
    
    Attributes:
        delivered (str): Notification has been delivered.
        viewed (str): Notification has been viewed by recipient.
    """
    delivered = "delivered"
    viewed = "viewed"

class NotificationType(str, Enum):
    """Enumeration for notification type categories.
    
    Attributes:
        announcement (str): General announcement to users/admins.
        broadcast (str): Broadcast message.
        reminder (str): Reminder notification.
        message (str): Direct message.
        in_app (str): In-app notification.
        email (str): Email notification.
    """
    announcement = "announcement"
    broadcast = "broadcast"
    reminder = "reminder"
    message = "message"
    in_app = "in-app"
    email = "email"

class NotificationCreate(BaseModel):
    """Schema for creating a new notification.
    
    Attributes:
        description (str): Notification message content.
        recipient_type (RecipientType): Type of recipient(s).
        recipient_id (Optional[int]): Specific user/admin ID if targeted notification.
        type (NotificationType): Category of notification.
        attachments (Optional[Dict[str, Any]]): Optional attachments/metadata.
        scheduled_at (Optional[datetime]): Schedule notification for future delivery.
    """
    description: str = Field(..., description="Notification message")
    recipient_type: RecipientType
    recipient_id: Optional[int] = Field(None, description="Specific user/admin ID if targeted")
    type: NotificationType
    attachments: Optional[Dict[str, Any]] = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None

class NotificationInDB(BaseModel):
    """Complete notification record as stored in database.
    
    Attributes:
        id (PyObjectId): MongoDB ObjectId stored as string in alias "_id".
        sender_type (SenderType): Who sent the notification.
        description (str): Message content.
        recipient_type (RecipientType): Type of recipient(s).
        recipient_id (Optional[int]): Specific recipient ID if targeted.
        status (NotificationStatus): Delivery/viewing status.
        type (NotificationType): Category of notification.
        attachments (Dict[str, Any]): Attached data/metadata.
        created_at (datetime): When notification was created.
        scheduled_at (Optional[datetime]): When scheduled for delivery.
    """
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    sender_type: SenderType
    description: str
    recipient_type: RecipientType
    recipient_id: Optional[int]
    status: NotificationStatus
    type: NotificationType
    attachments: Dict[str, Any]
    created_at: datetime
    scheduled_at: Optional[datetime]

    class Config:
        from_attributes = True

class NotificationResponse(NotificationInDB):
    """Notification response for API endpoints.
    
    Inherits all fields from NotificationInDB for API responses.
    """
    pass

class AnnouncementCreate(BaseModel):
    """Schema for creating an announcement (broadcast notification).
    
    Attributes:
        description (str): Announcement message content.
        attachments (Optional[Dict[str, Any]]): Optional attachments/media.
        scheduled_at (Optional[datetime]): Schedule announcement for future delivery.
        recipient_type (AnnouncementRecipientType): Target recipient group.
    """
    description: str
    attachments: Optional[Dict[str, Any]] = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None
    recipient_type: AnnouncementRecipientType

class NotificationMarkViewed(BaseModel):
    """Schema for marking a notification as viewed.
    
    Attributes:
        id (str): ID of the notification to mark as viewed.
    """
    id: str

class NotificationDelete(BaseModel):
    """Schema for deleting a notification.
    
    Attributes:
        id (str): ID of the notification to delete.
    """
    id: str