# schemas/notification.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, GetJsonSchemaHandler
from datetime import datetime
from enum import Enum
from typing import Literal
from pydantic_core import core_schema
from bson import ObjectId


class PyObjectId(ObjectId):
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
    system = "system"
    admin = "admin"

class AnnouncementRecipientType(str, Enum):
    all_admin = "all_admin"
    all_users = "all_users"
    prepaid_users = "prepaid_users"
    postpaid_users = "postpaid_users"
    blocked = "blocked"

class RecipientType(str, Enum):
    admin = "admin"
    all_admin = "all_admin"
    user = "user"
    all_users = "all_user"
    prepaid_users = "prepaid_users"
    postpaid_users = "postpaid_users"
    blocked = "blocked"

class NotificationStatus(str, Enum):
    delivered = "delivered"
    viewed = "viewed"

class NotificationType(str, Enum):
    announcement = "announcement"
    broadcast = "broadcast"
    reminder = "reminder"
    message = "message"
    in_app = "in-app"

class NotificationCreate(BaseModel):
    description: str = Field(..., description="Notification message")
    recipient_type: RecipientType
    recipient_id: Optional[int] = Field(None, description="Specific user/admin ID if targeted")
    type: NotificationType
    attachments: Optional[Dict[str, Any]] = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None

class NotificationInDB(BaseModel):
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
    pass

class AnnouncementCreate(BaseModel):
    description: str
    attachments: Optional[Dict[str, Any]] = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None
    recipient_type: AnnouncementRecipientType

class NotificationMarkViewed(BaseModel):
    id: str

class NotificationDelete(BaseModel):
    id: str