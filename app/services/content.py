from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import UploadFile, Depends
from ..crud.content import ContentCRUD
from ..utils.content import save_upload_file, delete_image_file
from ..models.admins import Admin
from bson import ObjectId

class ContentService:
    """
    Service for managing content documents and associated media files.

    This service coordinates file persistence (via `save_upload_file`),
    deletion of images and CRUD operations through the provided ContentCRUD
    implementation.
    """
    def __init__(self, crud: ContentCRUD):
        """
        Initialize ContentService with a CRUD implementation.

        Args:
            crud (ContentCRUD): Object implementing content persistence methods.
        """
        self.crud = crud

    async def create_content(
        self,
        content_type: str,
        title: str,
        body: Optional[str],
        image: Optional[UploadFile],
        current_user: Admin
    ):
        """
        Create a content document and persist an optional uploaded image.

        Args:
            content_type (str): Type/category of the content (e.g., "announcement").
            title (str): Content title.
            body (Optional[str]): Optional body/html text.
            image (Optional[UploadFile]): Optional uploaded image to be saved.
            current_user (Admin): Admin performing the creation.

        Returns:
            The document returned by the `ContentCRUD.create` call.

        Raises:
            HTTPException: If image saving fails (propagated from `save_upload_file`).
        """
        image_filename, image_url = await save_upload_file(image) if image else (None, None)

        now = datetime.now()
        data = {
            "content_type": content_type,
            "title": title,
            "body": body,
            "image_url": image_url,
            "image_filename": image_filename,
            "created_by": current_user.admin_id,
            "created_at": now,
            "updated_by": current_user.admin_id,
            "updated_at": now            
        }
        return await self.crud.create(data)

    async def update_content(
        self,
        content_id: ObjectId,
        content_type: Optional[str],
        title: Optional[str],
        body: Optional[str],
        image: Optional[UploadFile],
        current_user: Admin
    ):
        """
        Update an existing content document and replace its image if provided.

        Args:
            content_id (ObjectId): ID of the content document to update.
            content_type (Optional[str]): New content type or None to leave unchanged.
            title (Optional[str]): New title or None.
            body (Optional[str]): New body or None.
            image (Optional[UploadFile]): Replacement image to save; existing image will be removed.
            current_user (Admin): Admin performing the update.

        Returns:
            The updated document returned by `ContentCRUD.update`, or the existing
            document if no fields were changed, or None if the document was not found.

        Raises:
            HTTPException: If saving the new image fails (propagated from `save_upload_file`).
        """
        existing = await self.crud.get_by_id(content_id)
        if not existing:
            return None

        update_data: Dict[str, Any] = {}
        if content_type is not None:
            update_data["content_type"] = content_type
        if title is not None:
            update_data["title"] = title
        if body is not None:
            update_data["body"] = body

        if image and image.filename:
            # Delete old image
            delete_image_file(existing.get("image_filename"))
            new_filename, new_url = await save_upload_file(image)
            update_data["image_url"] = new_url
            update_data["image_filename"] = new_filename

        if not update_data:
            return existing  # No changes

        update_data["updated_at"] = datetime.now()
        update_data["updated_by"] = current_user.admin_id

        return await self.crud.update(content_id, update_data)

    async def delete_content(self, content_id: str):
        """
        Delete a content document and its associated image file if present.

        Args:
            content_id (str): Identifier of the content document to delete.

        Returns:
            The deleted document as returned by `ContentCRUD.delete`, or None if not found.
        """
        doc = await self.crud.delete(content_id)
        if doc:
            delete_image_file(doc.get("image_filename"))
        return doc