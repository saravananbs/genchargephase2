from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from datetime import datetime
from typing import Optional, Dict, Any, List
from ..schemas.content import ContentResponseAdmin, ContentResponseUser

def content_doc_to_admin_response(doc: dict) -> ContentResponseAdmin:
    return ContentResponseAdmin(
        _id=doc["_id"],
        content_type=doc["content_type"],
        title=doc["title"],
        body=doc.get("body"),
        image_url=doc.get("image_url"),
        image_filename=doc.get("image_filename"),
        created_by=doc["created_by"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
        updated_by=doc["updated_by"]
    )

def content_doc_to_user_response(doc: dict) -> ContentResponseUser:
    return ContentResponseUser(
        title=doc["title"],
        body=doc.get("body"),
        image_url=doc.get("image_url")
    )

class ContentCRUD:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    def content_doc_to_admin_response(self, doc: dict) -> ContentResponseAdmin:
        return ContentResponseAdmin(
            _id=doc["_id"],
            content_type=doc["content_type"],
            title=doc["title"],
            body=doc.get("body"),
            image_url=doc.get("image_url"),
            image_filename=doc.get("image_filename"),
            created_by=doc["created_by"],
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
            updated_by=doc["updated_by"]
        )

    def content_doc_to_user_response(self, doc: dict) -> ContentResponseUser:
        return ContentResponseUser(
            title=doc["title"],
            body=doc.get("body"),
            image_url=doc.get("image_url")
        )

    async def create(self, data: Dict[str, Any]) -> ContentResponseAdmin:
        result = await self.collection.insert_one(data)
        doc = await self.collection.find_one({"_id": result.inserted_id})
        return content_doc_to_admin_response(doc)

    async def get_by_id(self, content_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(content_id):
            return None
        return await self.collection.find_one({"_id": ObjectId(content_id)})

    async def update(self, content_id: str, update_data: Dict[str, Any]) -> ContentResponseAdmin:
        await self.collection.update_one({"_id": ObjectId(content_id)}, {"$set": update_data})
        doc = await self.collection.find_one({"_id": ObjectId(content_id)})
        return content_doc_to_admin_response(doc)

    async def delete(self, content_id: str) -> dict:
        doc = await self.get_by_id(content_id)
        if doc:
            await self.collection.delete_one({"_id": ObjectId(content_id)})
        return doc

    async def list_admin(
        self,
        filters: Dict[str, Any],
        sort_field: str,
        sort_dir: int,
        skip: int,
        limit: int
    ) -> List[dict]:
        cursor = self.collection.find(filters).sort(sort_field, sort_dir).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def count(self, filters: Dict[str, Any]) -> int:
        return await self.collection.count_documents(filters)

    async def list_public(self, skip: int, limit: int) -> List[dict]:
        projection = {"title": 1, "body": 1, "image_url": 1}
        cursor = self.collection.find({}, projection).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)