from fastapi import FastAPI, HTTPException, Query, Depends, APIRouter, Path, Security
from typing import List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes
from ....core.document_db import get_mongo_db
from bson import ObjectId
from ....schemas.contact_form import (
    ContactFormCreate, ContactFormResponse,
    ContactFormUpdateResolved, ContactFormFilter
)
from ....schemas.contact_form import ContactId
from ....services.contact_form import (
    service_create_contact, service_list_contacts,
    service_update_resolved
)

router = APIRouter()

@router.post("/contacts/", response_model=ContactFormResponse)
async def create_contact_endpoint(
    form: ContactFormCreate,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    return await service_create_contact(db, form)

@router.get("/contacts/", response_model=List[ContactFormResponse])
async def list_contacts_endpoint(
    email: Optional[str] = Query(None, description="Filter by email"),
    start_date: Optional[datetime] = Query(None, description="Start date for created_at (inclusive)"),
    end_date: Optional[datetime] = Query(None, description="End date for created_at (inclusive)"),
    order: Optional[str] = Query("desc", regex="^(asc|desc)$", description="Order by created_at: asc or desc"),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    current_user=Depends(get_current_user),
    authorized=Security(require_scopes, scopes=["Contact-form:read"])
):
    filters = ContactFormFilter(
        email=email,
        start_date=start_date,
        end_date=end_date,
        order=order
    )
    return await service_list_contacts(db, filters)

@router.patch("/contacts/{contact_id}/resolved", response_model=ContactFormResponse)
async def update_resolved_endpoint(
    data: ContactFormUpdateResolved,
    contact_id: str = Path(
        ...,
        regex=r"^[0-9a-fA-F]{24}$",
        description="24-character hex MongoDB ObjectId",
        example="690b4d102db459363a40516a"
    ),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    current_user=Depends(get_current_user),
    authorized=Security(require_scopes, scopes=["Contact-form:write"])
):
    # Convert safely
    try:
        obj_id = ObjectId(contact_id)
    except:
        raise HTTPException(status_code=422, detail="Invalid ObjectId format")

    result = await service_update_resolved(db, obj_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Contact not found")
    return result