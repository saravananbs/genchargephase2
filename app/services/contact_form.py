# services.py
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..schemas.contact_form import ContactFormCreate, ContactFormResponse, ContactFormFilter, ContactFormUpdateResolved
from ..crud.contact_form import create_contact, get_contacts, update_resolved
from bson import ObjectId

async def service_create_contact(db: AsyncIOMotorDatabase, form: ContactFormCreate) -> ContactFormResponse:
    return await create_contact(db, form)

async def service_list_contacts(
    db: AsyncIOMotorDatabase,
    filters: ContactFormFilter
) -> List[ContactFormResponse]:
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
    return await update_resolved(db, contact_id, data.resolved)