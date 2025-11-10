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
    """
    Submit a new contact form / support ticket.
    
    Allows users to submit support requests, feedback, bug reports, or inquiries
    through a contact form. Tickets are tracked and routed to support team for
    response. Confirmation email is sent to submitter. No authentication required.
    
    Security:
        - No JWT required (public endpoint)
        - Rate limiting: 10 submissions per hour per email
        - CAPTCHA verification recommended on frontend
    
    Request Body:
        ContactFormCreate (JSON):
            - name (str): Full name of submitter (required, 1-100 chars)
            - email (str): Email address (required, valid format)
            - phone (str, optional): Phone number (E.164 format)
            - subject (str): Ticket subject (required, 5-200 chars)
            - message (str): Detailed message/description (required, 10-5000 chars)
            - category (str): Ticket category (bug, feedback, support, inquiry, billing)
            - priority (str, optional): Priority level (low, medium, high, urgent)
    
    Returns:
        ContactFormResponse:
            - id (str): MongoDB ObjectId as string
            - name (str): Submitter name
            - email (str): Submitter email
            - phone (str, optional): Submitter phone
            - subject (str): Ticket subject
            - message (str): Ticket message
            - category (str): Ticket category
            - priority (str): Priority level
            - status (str): Initial status (new/open)
            - resolved (bool): Always false for new tickets
            - created_at (datetime): Submission timestamp
            - ticket_id (str): Human-readable ticket reference
    
    Raises:
        HTTPException(400): Invalid form data or validation error
        HTTPException(422): Email format invalid
        HTTPException(429): Too many submissions from this email
    
    Example:
        Request:
            POST /contact-form/contacts/
            Body:
            {
                "name": "John User",
                "email": "john@example.com",
                "subject": "Plan renewal not working",
                "message": "I tried to renew my plan but got error code 500",
                "category": "bug",
                "priority": "high"
            }
        
        Response (201 Created):
            {
                "id": "690b4d102db459363a40516a",
                "name": "John User",
                "email": "john@example.com",
                "subject": "Plan renewal not working",
                "message": "I tried to renew my plan but got error code 500",
                "category": "bug",
                "priority": "high",
                "status": "open",
                "resolved": false,
                "created_at": "2024-01-20T10:00:00Z",
                "ticket_id": "TKT-001234"
            }
    """
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
    """
    List all submitted contact forms / support tickets.
    
    Retrieves all support tickets with optional filtering by submitter email
    and date range. Used by support team to manage and respond to tickets.
    Results are sorted by submission date.
    
    Security:
        - Requires valid JWT access token
        - Scope: Contact-form:read
        - Restricted to admin/support team
    
    Query Parameters:
        - email (str, optional): Filter by submitter email (partial match)
        - start_date (datetime, optional): Filter tickets submitted after this date
        - end_date (datetime, optional): Filter tickets submitted before this date
        - order (str, optional): Sort order (asc/desc, default: desc)
            - desc: Most recent first
            - asc: Oldest first
    
    Returns:
        List[ContactFormResponse]: Array of contact form objects:
            - id (str): MongoDB ObjectId as string
            - name (str): Submitter name
            - email (str): Submitter email
            - phone (str, optional): Submitter phone
            - subject (str): Ticket subject
            - message (str): Ticket message
            - category (str): Category (bug, feedback, support, etc.)
            - priority (str): Priority level
            - status (str): Current status (open, in-progress, resolved, closed)
            - resolved (bool): Whether ticket is resolved
            - created_at (datetime): Submission timestamp
            - updated_at (datetime, optional): Last update timestamp
            - ticket_id (str): Human-readable reference
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Contact-form:read scope
        HTTPException(400): Invalid date format or filter parameters
    
    Example:
        Request:
            GET /contact-form/contacts/?email=john&start_date=2024-01-01&order=desc
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            [
                {
                    "id": "690b4d102db459363a40516a",
                    "name": "John User",
                    "email": "john@example.com",
                    "subject": "Plan renewal not working",
                    "message": "I tried to renew my plan but got error",
                    "category": "bug",
                    "priority": "high",
                    "status": "open",
                    "resolved": false,
                    "created_at": "2024-01-20T10:00:00Z",
                    "ticket_id": "TKT-001234"
                }
            ]
    """
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
    """
    Mark a support ticket as resolved / close ticket.
    
    Updates ticket status to resolved and optionally adds resolution notes
    or response message. Allows support team to close completed tickets.
    Sends confirmation email to submitter with resolution details.
    
    Security:
        - Requires valid JWT access token
        - Scope: Contact-form:write
        - Restricted to admin/support team
    
    Path Parameters:
        - contact_id (str): MongoDB ObjectId of ticket (24-char hex string)
            - Must be valid ObjectId format
            - Example: "690b4d102db459363a40516a"
    
    Request Body:
        ContactFormUpdateResolved (JSON):
            - resolved (bool): Mark as resolved (true)
            - resolution_notes (str, optional): Internal notes about resolution
            - response_message (str, optional): Message to send to submitter
    
    Returns:
        ContactFormResponse: Updated ticket with:
            - id (str): Ticket ID
            - name (str): Submitter name
            - email (str): Submitter email
            - subject (str): Original subject
            - message (str): Original message
            - resolved (bool): Now true
            - status (str): Updated to "resolved"
            - updated_at (datetime): Update timestamp
    
    Raises:
        HTTPException(400): Invalid ObjectId format
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Contact-form:write scope
        HTTPException(404): Contact form not found
        HTTPException(422): Invalid ObjectId
    
    Example:
        Request:
            PATCH /contact-form/contacts/690b4d102db459363a40516a/resolved
            Headers: Authorization: Bearer <jwt_token>
            Body:
            {
                "resolved": true,
                "resolution_notes": "Fixed in latest update",
                "response_message": "Thank you for reporting. This issue has been resolved in v2.1.0"
            }
        
        Response (200 OK):
            {
                "id": "690b4d102db459363a40516a",
                "name": "John User",
                "email": "john@example.com",
                "subject": "Plan renewal not working",
                "message": "I tried to renew my plan but got error",
                "category": "bug",
                "status": "resolved",
                "resolved": true,
                "created_at": "2024-01-20T10:00:00Z",
                "updated_at": "2024-01-20T11:30:00Z",
                "ticket_id": "TKT-001234"
            }
    """
    # Convert safely
    try:
        obj_id = ObjectId(contact_id)
    except:
        raise HTTPException(status_code=422, detail="Invalid ObjectId format")

    result = await service_update_resolved(db, obj_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Contact not found")
    return result