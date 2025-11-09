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
    return await service_create_announcement(db, payload, current_user)


@router.get("/my", response_model=List[NotificationResponse])
async def get_my_notifications(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Admin | User = Depends(get_current_user),
    # no ned of scopes cause any admin or user can get their noti
):
    return await service_get_my_notifications(db=db, current_user=current_user)
    

@router.delete("/delete")
async def delete_notification(
    payload: NotificationDelete,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User | Admin = Depends(get_current_user),
    # no need of scopes cause any admin or user can delete their noti
):
    return await service_delete_notification(db=db, current_user=current_user, payload=payload)