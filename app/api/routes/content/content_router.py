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
    """
    Create new content (blog post, FAQ, announcement, etc.).
    
    Allows admins to create CMS content with optional image upload. Supports
    multiple content types (blog, faq, help, announcement). Images are stored
    locally and served via static file endpoint. Content is published immediately.
    
    Security:
        - Requires valid JWT access token
        - Scope: Content:write
        - Restricted to admin/content team
    
    Form Parameters:
        - content_type (str): Type of content (blog, faq, help, announcement)
        - title (str): Content title (required, 1-200 chars)
        - body (str, optional): Content body (HTML or markdown, max 50000 chars)
        - image (file, optional): Featured image (jpg, png, webp, max 5MB)
    
    Returns:
        ContentResponseAdmin: Created content with:
            - id (str): MongoDB ObjectId
            - content_type (str): Content type
            - title (str): Title
            - body (str): Content body
            - image_url (str, optional): Image URL for serving
            - created_by (int): Admin ID who created
            - created_at (datetime): Creation timestamp
            - updated_at (datetime): Last update
    
    Raises:
        HTTPException(400): Invalid form data or file too large
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Content:write scope
        HTTPException(422): Invalid content type
    
    Example:
        Request:
            POST /content/admin
            Headers: 
              Authorization: Bearer <jwt_token>
              Content-Type: multipart/form-data
            Body:
              content_type: blog
              title: How to Renew Your Plan
              body: <p>Step 1: Open app...</p>
              image: [file]
        
        Response (201 Created):
            {
                "id": "690b4d102db459363a40516a",
                "content_type": "blog",
                "title": "How to Renew Your Plan",
                "body": "<p>Step 1: Open app...</p>",
                "image_url": "/static/uploads/content_123_image.jpg",
                "created_by": 1,
                "created_at": "2024-01-20T10:00:00Z",
                "updated_at": "2024-01-20T10:00:00Z"
            }
    """
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
    """
    Update existing content.
    
    Modifies content fields including title, body, type, and image. Allows
    partial updates - omitted fields are not changed. Updates are effective
    immediately. Previous image is deleted if new image is uploaded.
    
    Security:
        - Requires valid JWT access token
        - Scope: Content:edit
        - Restricted to admin/content team
    
    Path Parameters:
        - content_id (str): MongoDB ObjectId of content
    
    Form Parameters (all optional):
        - content_type (str): New content type (blog, faq, help, announcement)
        - title (str): New title (1-200 chars)
        - body (str): New content body (HTML, max 50000 chars)
        - image (file): New featured image (jpg, png, webp, max 5MB)
    
    Returns:
        ContentResponseAdmin: Updated content object
    
    Raises:
        HTTPException(400): Invalid form data or file error
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Content:edit scope
        HTTPException(404): Content not found
        HTTPException(422): Invalid ObjectId or content type
    
    Example:
        Request:
            PUT /content/admin/690b4d102db459363a40516a
            Headers: 
              Authorization: Bearer <jwt_token>
              Content-Type: multipart/form-data
            Body:
              title: How to Renew Your Plan - Updated Guide
              body: <p>Updated steps for 2024...</p>
        
        Response (200 OK):
            {
                "id": "690b4d102db459363a40516a",
                "content_type": "blog",
                "title": "How to Renew Your Plan - Updated Guide",
                "body": "<p>Updated steps for 2024...</p>",
                "updated_at": "2024-01-20T11:00:00Z"
            }
    """
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
    """
    List all content with advanced filtering and pagination (Admin view).
    
    Retrieves paginated list of all system content with support for filtering
    by title, creator, date ranges, and sorting. Used by content team to
    manage and organize website content.
    
    Security:
        - Requires valid JWT access token
        - Scope: Content:read
        - Restricted to admin/content team
    
    Query Parameters:
        - title (str, optional): Filter by title (case-insensitive partial match)
        - created_by (str, optional): Filter by creator admin ID
        - updated_by (str, optional): Filter by last editor admin ID
        - created_at_from (datetime, optional): Filter content created after date
        - created_at_to (datetime, optional): Filter content created before date
        - updated_at_from (datetime, optional): Filter content updated after date
        - updated_at_to (datetime, optional): Filter content updated before date
        - order_by (str, optional): Sort field (created_at, updated_at, default: created_at)
        - order_dir (str, optional): Sort direction (asc, desc, default: desc)
        - page (int, optional): Page number (default: 1, minimum: 1)
        - size (int, optional): Records per page (default: 10, max: 100)
    
    Returns:
        PaginatedResponseAdmin:
            - items (list): Array of content objects with admin fields
            - total (int): Total content count matching filters
            - page (int): Current page number
            - size (int): Records per page
            - pages (int): Total pages
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Content:read scope
        HTTPException(400): Invalid filter or pagination parameters
    
    Example:
        Request:
            GET /content/admin?title=plan&order_by=updated_at&order_dir=desc&page=1&size=20
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            {
                "items": [
                    {
                        "id": "690b4d102db459363a40516a",
                        "content_type": "blog",
                        "title": "How to Renew Your Plan",
                        "created_by": 1,
                        "created_at": "2024-01-20T10:00:00Z",
                        "updated_at": "2024-01-20T11:00:00Z"
                    }
                ],
                "total": 5,
                "page": 1,
                "size": 20,
                "pages": 1
            }
    """
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
    """
    List all public content (visible to end users).
    
    Retrieves paginated list of published CMS content (blog posts, FAQs, help articles,
    announcements) displayed on the app and website. Public endpoint requiring no
    authentication. Content is sorted by recency.
    
    Security:
        - No authentication required (public endpoint)
        - All users can access this endpoint
    
    Query Parameters:
        - page (int, optional): Page number (default: 1, minimum: 1)
        - size (int, optional): Records per page (default: 10, max: 100)
    
    Returns:
        PaginatedResponseUser:
            - items (list): Array of public content objects:
                - id (str): Content ID
                - content_type (str): Type (blog, faq, help, announcement)
                - title (str): Content title
                - body (str): Content body
                - image_url (str, optional): Featured image URL
                - created_at (datetime): Publication date
            - total (int): Total content count
            - page (int): Current page
            - size (int): Records per page
            - pages (int): Total pages
    
    Raises:
        HTTPException(400): Invalid pagination parameters
    
    Example:
        Request:
            GET /content?page=1&size=10
        
        Response (200 OK):
            {
                "items": [
                    {
                        "id": "690b4d102db459363a40516a",
                        "content_type": "blog",
                        "title": "How to Renew Your Plan",
                        "body": "<p>Step 1: Open app...</p>",
                        "image_url": "/static/uploads/content_123.jpg",
                        "created_at": "2024-01-20T10:00:00Z"
                    },
                    {
                        "id": "690b4d102db459363a40516b",
                        "content_type": "faq",
                        "title": "How do I check my balance?",
                        "body": "<p>Your balance is shown in the dashboard...</p>",
                        "created_at": "2024-01-19T15:00:00Z"
                    }
                ],
                "total": 45,
                "page": 1,
                "size": 10,
                "pages": 5
            }
    """
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
    """
    Delete content permanently.
    
    Removes content from CMS. Associated images are also deleted from storage.
    This action is permanent and cannot be undone. Deletion is logged for audit.
    
    Security:
        - Requires valid JWT access token
        - Scope: Content:delete
        - Restricted to admin/content team
    
    Path Parameters:
        - content_id (str): MongoDB ObjectId of content to delete
    
    Returns:
        dict: Deletion confirmation:
            {
                "message": "Content <id> deleted successfully"
            }
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Content:delete scope
        HTTPException(404): Content not found
        HTTPException(422): Invalid ObjectId format
    
    Example:
        Request:
            DELETE /content/admin/690b4d102db459363a40516a
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            {
                "message": "Content 690b4d102db459363a40516a deleted successfully"
            }
    """
    doc = await service.delete_content(content_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Content not found")
    return {"message": f"Content {content_id} deleted successfully"}