from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status, Security
from typing import Optional
from datetime import datetime
from ....dependencies.permissions import require_scopes
from ....dependencies.auth import get_current_user
from ....core.document_db import get_mongo_db as get_db
from ....models.admins import Admin
from ....schemas.content import (
    ContentResponseAdmin, PaginatedResponseAdmin,
    ContentResponseUser, PaginatedResponseUser, ContentType
)
from ....crud.content import ContentCRUD
from ....services.content import ContentService
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi.staticfiles import StaticFiles
import os
from bson import ObjectId

router = APIRouter()
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
router.mount("/static", StaticFiles(directory="static"), name="static")

def get_crud(db: AsyncIOMotorDatabase = Depends(get_db)):
    return ContentCRUD(db["content"])

def get_service(crud: ContentCRUD = Depends(get_crud)):
    return ContentService(crud)

# === ADMIN: CREATE ===
@router.post(
    "/admin",
    response_model=ContentResponseAdmin,
    status_code=status.HTTP_201_CREATED,
    summary="Admin: Create content"
)
async def create_content(
    content_type: ContentType = Form(...),
    title: str = Form(...),
    body: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    service: ContentService = Depends(get_service),
    current_user: Admin = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Content:write"])
):
    print(current_user.admin_id)
    return await service.create_content(content_type, title, body, image, current_user)


# === ADMIN: UPDATE ===
@router.put(
    "/admin/{content_id}",
    response_model=ContentResponseAdmin,
    summary="Admin: Edit content"
)
async def update_content(
    content_id: str,
    content_type: Optional[ContentType] = Form(None),
    title: Optional[str] = Form(None),
    body: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    service: ContentService = Depends(get_service),
    current_user: Admin = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Content:edit"])
):
    result = await service.update_content(content_id, content_type, title, body, image, current_user)
    if not result:
        raise HTTPException(status_code=404, detail="Content not found")
    return result


# === ADMIN: LIST WITH FILTERS ===
@router.get(
    "/admin",
    response_model=PaginatedResponseAdmin,
    summary="Admin: List with filters, sort, pagination"
)
async def list_contents_admin(
    title: Optional[str] = Query(None),
    created_by: Optional[str] = Query(None),
    updated_by: Optional[str] = Query(None),
    created_at_from: Optional[datetime] = Query(None),
    created_at_to: Optional[datetime] = Query(None),
    updated_at_from: Optional[datetime] = Query(None),
    updated_at_to: Optional[datetime] = Query(None),
    order_by: Optional[str] = Query("created_at", regex="^(created_at|updated_at)$"),
    order_dir: Optional[str] = Query("desc", regex="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    crud: ContentCRUD = Depends(get_crud),
    current_user: Admin = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Content:read"])
):
    filters = {}
    if title:
        filters["title"] = {"$regex": title, "$options": "i"}
    if created_by:
        filters["created_by"] = created_by
    if updated_by:
        filters["updated_by"] = updated_by
    if created_at_from:
        filters.setdefault("created_at", {})["$gte"] = created_at_from
    if created_at_to:
        filters.setdefault("created_at", {})["$lte"] = created_at_to
    if updated_at_from:
        filters.setdefault("updated_at", {})["$gte"] = updated_at_from
    if updated_at_to:
        filters.setdefault("updated_at", {})["$lte"] = updated_at_to

    sort_dir = -1 if order_dir == "desc" else 1
    skip = (page - 1) * size

    total = await crud.count(filters)
    docs = await crud.list_admin(filters, order_by, sort_dir, skip, size)
    items = [crud.content_doc_to_admin_response(doc) for doc in docs]
    pages = (total + size - 1) // size if total > 0 else 1

    return PaginatedResponseAdmin(items=items, total=total, page=page, size=size, pages=pages)


# === USER: LIST PUBLIC ===
@router.get(
    "",
    response_model=PaginatedResponseUser,
    summary="Users: List public content"
)
async def list_contents_public(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    crud: ContentCRUD = Depends(get_crud)
):
    skip = (page - 1) * size
    total = await crud.count({})
    docs = await crud.list_public(skip, size)
    items = [crud.content_doc_to_user_response(doc) for doc in docs]
    pages = (total + size - 1) // size if total > 0 else 1

    return PaginatedResponseUser(items=items, total=total, page=page, size=size, pages=pages)


# === ADMIN: DELETE ===
@router.delete(
    "/admin/{content_id}",
    status_code=status.HTTP_200_OK,
    summary="Admin: Delete content"
)
async def delete_content(
    content_id: str,
    service: ContentService = Depends(get_service),
    current_user: Admin = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Content:delete"])
):
    doc = await service.delete_content(content_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Content not found")
    return {"message": f"Content {content_id} deleted successfully"}