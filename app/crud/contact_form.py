# crud.py
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from typing import List, Optional
from ..schemas.contact_form import ContactFormCreate, ContactFormResponse, ContactFormFilter
from fastapi import HTTPException

COLLECTION_NAME = "contact_forms"

async def create_contact(db: AsyncIOMotorDatabase, form: ContactFormCreate) -> ContactFormResponse:
    """
    Create a new contact form submission in MongoDB.

    Args:
        db (AsyncIOMotorDatabase): Motor async database instance.
        form (ContactFormCreate): Contact form data to create.

    Returns:
        ContactFormResponse: The created contact form with generated ID and timestamp.
    """
    doc = form.model_dump()
    doc["created_at"] = datetime.now()
    doc["resolved"] = False
    result = await db[COLLECTION_NAME].insert_one(doc)
    created = await db[COLLECTION_NAME].find_one({"_id": result.inserted_id})
    return ContactFormResponse(**created)

async def get_contacts(
    db: AsyncIOMotorDatabase,
    email: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    order: str = "desc"
) -> List[ContactFormResponse]:
    """
    Retrieve contact form submissions with optional filtering and sorting.

    Args:
        db (AsyncIOMotorDatabase): Motor async database instance.
        email (Optional[str]): Filter by email address.
        start_date (Optional[datetime]): Filter by start date (inclusive).
        end_date (Optional[datetime]): Filter by end date (inclusive).
        order (str): Sort order, "desc" for descending or "asc" for ascending (default: "desc").

    Returns:
        List[ContactFormResponse]: List of contact form submissions matching criteria.
    """
    query = {}
    if email:
        query["email"] = email
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        query["created_at"] = date_filter

    sort_order = -1 if order == "desc" else 1
    cursor = db[COLLECTION_NAME].find(query).sort("created_at", sort_order)
    results = await cursor.to_list(length=1000)
    return [ContactFormResponse(**doc) for doc in results]

async def update_resolved(
    db: AsyncIOMotorDatabase,
    contact_id: ObjectId,       
    resolved: bool
) -> Optional[ContactFormResponse]:
    """
    Update the resolved status of a contact form submission.

    Args:
        db (AsyncIOMotorDatabase): Motor async database instance.
        contact_id (ObjectId): MongoDB ObjectId of the contact form.
        resolved (bool): New resolved status.

    Returns:
        Optional[ContactFormResponse]: Updated contact form, or None if update failed.

    Raises:
        HTTPException: If the contact form was not found or could not be updated.
    """
    result = await db[COLLECTION_NAME].update_one(
        {"_id": contact_id},
        {"$set": {"resolved": resolved}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=401, detail="No changes done")
    updated = await db[COLLECTION_NAME].find_one({"_id": contact_id})
    return ContactFormResponse(**updated)