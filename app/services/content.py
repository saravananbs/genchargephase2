from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import UploadFile, Depends
from ..crud.content import ContentCRUD
from ..utils.content import save_upload_file, delete_image_file
from ..models.admins import Admin
from bson import ObjectId

class ContentService:
    def __init__(self, crud: ContentCRUD):
        self.crud = crud

    async def create_content(
        self,
        content_type: str,
        title: str,
        body: Optional[str],
        image: Optional[UploadFile],
        current_user: Admin
    ):
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
        doc = await self.crud.delete(content_id)
        if doc:
            delete_image_file(doc.get("image_filename"))
        return doc