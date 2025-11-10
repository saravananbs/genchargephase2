# services.py
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..schemas.contact_form import ContactFormCreate, ContactFormResponse, ContactFormFilter, ContactFormUpdateResolved
from ..crud.contact_form import create_contact, get_contacts, update_resolved
from bson import ObjectId

async def service_create_contact(db: AsyncIOMotorDatabase, form: ContactFormCreate) -> ContactFormResponse:
    """
    Persist a new contact form submission to the document store.

    Args:
        db (AsyncIOMotorDatabase): Motor async database instance.
        form (ContactFormCreate): Contact form payload to save.

    Returns:
        ContactFormResponse: The saved contact form document as a response DTO.
    """
    return await create_contact(db, form)

async def service_list_contacts(
    db: AsyncIOMotorDatabase,
    filters: ContactFormFilter
) -> List[ContactFormResponse]:
    """
    Retrieve contact form submissions matching the provided filters.

    Args:
        db (AsyncIOMotorDatabase): Motor async database instance.
        filters (ContactFormFilter): Filtering and ordering options.

    Returns:
        List[ContactFormResponse]: List of matching contact form response DTOs.
    """
    return await get_contacts(
        db,
        email=filters.email,
        start_date=filters.start_date,
        end_date=filters.end_date,
        order=filters.order
    )

async def service_update_resolved(
    db: AsyncIOMotorDatabase,
    contact_id: ObjectId,
    data: ContactFormUpdateResolved
) -> Optional[ContactFormResponse]:
    """
    Mark a contact form entry as resolved or unresolved.

    Args:
        db (AsyncIOMotorDatabase): Motor async database instance.
        contact_id (ObjectId): Identifier of the contact document to update.
        data (ContactFormUpdateResolved): Payload containing the resolved flag.

    Returns:
        Optional[ContactFormResponse]: Updated contact form document if successful, else None.
    """
    return await update_resolved(db, contact_id, data.resolved)