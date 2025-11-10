from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from datetime import datetime
from typing import Optional, Dict, Any, List
from ..schemas.content import ContentResponseAdmin, ContentResponseUser

def content_doc_to_admin_response(doc: dict) -> ContentResponseAdmin:
    """
    Convert a MongoDB content document to admin response schema.

    Args:
        doc (dict): MongoDB document containing content data.

    Returns:
        ContentResponseAdmin: Content data formatted for admin view.
    """
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
    """
    Convert a MongoDB content document to user response schema.

    Includes only publicly visible fields (title, body, image_url).

    Args:
        doc (dict): MongoDB document containing content data.

    Returns:
        ContentResponseUser: Content data formatted for public/user view.
    """
    return ContentResponseUser(
        title=doc["title"],
        body=doc.get("body"),
        image_url=doc.get("image_url")
    )

class ContentCRUD:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    def content_doc_to_admin_response(self, doc: dict) -> ContentResponseAdmin:
        """
        Convert a MongoDB content document to admin response schema (instance method).

        Args:
            doc (dict): MongoDB document containing content data.

        Returns:
            ContentResponseAdmin: Content data formatted for admin view.
        """
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
        """
        Convert a MongoDB content document to user response schema (instance method).

        Includes only publicly visible fields (title, body, image_url).

        Args:
            doc (dict): MongoDB document containing content data.

        Returns:
            ContentResponseUser: Content data formatted for public/user view.
        """
        return ContentResponseUser(
            title=doc["title"],
            body=doc.get("body"),
            image_url=doc.get("image_url")
        )

    async def create(self, data: Dict[str, Any]) -> ContentResponseAdmin:
        """
        Create a new content document in MongoDB.

        Args:
            data (Dict[str, Any]): Content data to insert.

        Returns:
            ContentResponseAdmin: Newly created content formatted for admin view.
        """
        result = await self.collection.insert_one(data)
        doc = await self.collection.find_one({"_id": result.inserted_id})
        return content_doc_to_admin_response(doc)

    async def get_by_id(self, content_id: str) -> Optional[dict]:
        """
        Retrieve a content document by its MongoDB ID.

        Args:
            content_id (str): Content ID as string.

        Returns:
            Optional[dict]: Content document if found, None otherwise.
        """
        if not ObjectId.is_valid(content_id):
            return None
        return await self.collection.find_one({"_id": ObjectId(content_id)})

    async def update(self, content_id: str, update_data: Dict[str, Any]) -> ContentResponseAdmin:
        """
        Update a content document by ID.

        Args:
            content_id (str): Content ID as string.
            update_data (Dict[str, Any]): Fields to update.

        Returns:
            ContentResponseAdmin: Updated content formatted for admin view.
        """
        await self.collection.update_one({"_id": ObjectId(content_id)}, {"$set": update_data})
        doc = await self.collection.find_one({"_id": ObjectId(content_id)})
        return content_doc_to_admin_response(doc)

    async def delete(self, content_id: str) -> dict:
        """
        Delete a content document by ID.

        Args:
            content_id (str): Content ID as string.

        Returns:
            dict: The deleted content document, or None if not found.
        """
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
        """
        Retrieve paginated content documents with filtering and sorting (admin view).

        Args:
            filters (Dict[str, Any]): MongoDB query filters.
            sort_field (str): Field to sort by.
            sort_dir (int): Sort direction (1 for ascending, -1 for descending).
            skip (int): Number of documents to skip.
            limit (int): Maximum number of documents to return.

        Returns:
            List[dict]: Filtered and paginated content documents.
        """
        cursor = self.collection.find(filters).sort(sort_field, sort_dir).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def count(self, filters: Dict[str, Any]) -> int:
        """
        Count content documents matching given filters.

        Args:
            filters (Dict[str, Any]): MongoDB query filters.

        Returns:
            int: Total count of documents matching filters.
        """
        return await self.collection.count_documents(filters)

    async def list_public(self, skip: int, limit: int) -> List[dict]:
        """
        Retrieve paginated public content (user view) with limited fields.

        Returns only title, body, and image_url fields, ordered by creation date descending.

        Args:
            skip (int): Number of documents to skip.
            limit (int): Maximum number of documents to return.

        Returns:
            List[dict]: Public content documents with limited fields.
        """
        projection = {"title": 1, "body": 1, "image_url": 1}
        cursor = self.collection.find({}, projection).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)