from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, Query, HTTPException, Security
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes
from ....models.users import User
from ....schemas.autopay import (
    AutoPayCreate,
    AutoPayUpdate,
    AutoPayOut,
    PaginatedAutoPay,
    PaginatedAutoPayAdmin,
    AutoPayStatus,
    AutoPayTag,
)
from ....schemas.autopay_credentials import (
    AutoPayCredentialOut,
    AutoPayCredentialUpsert,
)
from app.services.autopay import (
    create_user_autopay,
    get_user_autopay,
    list_user_autopays,
    update_user_autopay,
    delete_user_autopay,
    list_all_autopays,
    process_due_autopays,
)
from app.services.autopay_credentials import (
    fetch_user_autopay_credentials,
    replace_user_autopay_credentials,
)

router = APIRouter()


# ====================== USER ENDPOINTS ======================
@router.post("/create_autopay", response_model=AutoPayOut, status_code=201)
async def add_autopay(
    payload: AutoPayCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"])
):
    """
    Create a new autopay rule for the current user.
    
    Allows users to set up automatic recurring recharges on specified schedules.
    Autopay rules enable convenient hands-free plan renewals and wallet top-ups
    at configurable intervals. Rules can be paused or deleted anytime.
    
    Security:
        - Requires valid JWT access token
        - Scope: User
        - Users can only create autopay for their own account
    
    Request Body:
        AutoPayCreate (JSON):
            - plan_id (int): Plan to auto-recharge (must exist)
            - frequency (str): Recurrence pattern (daily, weekly, monthly, quarterly, yearly)
            - amount (float): Amount to auto-recharge (if wallet top-up)
            - phone_number (str): Phone number for recharge (E.164 format)
            - next_due_date (datetime): When to trigger first autopay
            - tag (str, optional): Custom tag for organization (e.g., "work", "personal")
            - notes (str, optional): User notes about this autopay
    
    Returns:
        AutoPayOut: Created autopay rule with:
            - autopay_id (int): Unique identifier
            - user_id (int): Owner user ID
            - plan_id (int): Associated plan
            - frequency (str): Recurrence pattern
            - next_due_date (datetime): Next execution date
            - status (str): Status (active, paused, completed)
            - created_at (datetime): Creation timestamp
    
    Raises:
        HTTPException(400): Invalid plan ID or parameter validation error
        HTTPException(401): User not authenticated
        HTTPException(403): Missing User scope
        HTTPException(404): Plan not found
        HTTPException(409): Autopay already exists for this configuration
    
    Example:
        Request:
            POST /autopay/create_autopay
            Headers: Authorization: Bearer <jwt_token>
            Body:
            {
                "plan_id": 5,
                "frequency": "monthly",
                "phone_number": "+919876543210",
                "next_due_date": "2024-02-20T10:00:00Z",
                "tag": "work"
            }
        
        Response (201 Created):
            {
                "autopay_id": 12,
                "user_id": 42,
                "plan_id": 5,
                "frequency": "monthly",
                "next_due_date": "2024-02-20T10:00:00Z",
                "status": "active",
                "tag": "work",
                "created_at": "2024-01-20T10:00:00Z"
            }
    """
    return await create_user_autopay(db, obj_in=payload, current_user_id=current_user.user_id)


@router.get("/get_autopay/{autopay_id}", response_model=AutoPayOut)
async def get_one_autopay(
    autopay_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"])
):
    """
    Retrieve details of a specific autopay rule.
    
    Fetch detailed information about a single autopay configuration including
    schedule, next execution date, payment source, and current status.
    
    Security:
        - Requires valid JWT access token
        - Scope: User
        - Users can only view their own autopay rules
    
    Path Parameters:
        - autopay_id (int): ID of autopay to retrieve (must belong to current user)
    
    Returns:
        AutoPayOut: Autopay details:
            - autopay_id (int): Unique identifier
            - user_id (int): Owner user ID
            - plan_id (int): Associated plan
            - phone_number (str): Phone number for recharge
            - frequency (str): Recurrence pattern
            - next_due_date (datetime): Next execution date
            - status (str): Current status (active/paused/completed)
            - tag (str): Organization tag
            - notes (str): User notes
            - created_at (datetime): Creation timestamp
            - updated_at (datetime): Last modification
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Autopay does not belong to current user
        HTTPException(404): Autopay not found
    
    Example:
        Request:
            GET /autopay/get_autopay/12
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            {
                "autopay_id": 12,
                "user_id": 42,
                "plan_id": 5,
                "phone_number": "+919876543210",
                "frequency": "monthly",
                "next_due_date": "2024-02-20T10:00:00Z",
                "status": "active",
                "tag": "work",
                "notes": "Monthly work phone recharge",
                "created_at": "2024-01-20T10:00:00Z",
                "updated_at": "2024-01-20T10:00:00Z"
            }
    """
    return await get_user_autopay(db, autopay_id=autopay_id, current_user_id=current_user.user_id)


@router.get("/get_all_autopay", response_model=PaginatedAutoPay)
async def list_my_autopays(
    page: int = Query(0, ge=0),
    size: int = Query(0, ge=0, le=100),
    status: AutoPayStatus | None = None,
    phone_number: str | None = None,
    tag: AutoPayTag | None = None,
    sort: Literal[
        "created_at_desc",
        "created_at_asc",
        "next_due_date_desc",
        "next_due_date_asc",
    ] = "created_at_desc",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"])
):
    """
    List all autopay rules for the current user with filtering and sorting.
    
    Retrieves paginated list of all autopay rules belonging to the current user.
    Supports filtering by status, phone number, and tags. Results are sorted
    by creation date or next due date as specified.
    
    Security:
        - Requires valid JWT access token
        - Scope: User
        - Users can only view their own autopay rules
    
    Query Parameters:
        - page (int, optional): Page number (default: 1, minimum: 1)
        - size (int, optional): Records per page (default: 20, max: 100)
        - status (str, optional): Filter by status (active, paused, completed)
        - phone_number (str, optional): Filter by phone number (partial match)
        - tag (str, optional): Filter by tag (exact match)
        - sort (str, optional): Sorting order:
            - created_at_desc: Newest first (default)
            - created_at_asc: Oldest first
            - next_due_date_desc: Due later first
            - next_due_date_asc: Due sooner first
    
    Returns:
        PaginatedAutoPay:
            - items (list): Array of AutoPayOut objects
            - total (int): Total count of user's autopays
            - page (int): Current page number
            - size (int): Records per page
            - pages (int): Total pages
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing User scope
        HTTPException(400): Invalid pagination or filter parameters
    
    Example:
        Request:
            GET /autopay/get_all_autopay?page=1&size=10&status=active&sort=next_due_date_asc
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            {
                "items": [
                    {
                        "autopay_id": 12,
                        "user_id": 42,
                        "plan_id": 5,
                        "phone_number": "+919876543210",
                        "frequency": "monthly",
                        "next_due_date": "2024-02-20T10:00:00Z",
                        "status": "active",
                        "tag": "work",
                        "created_at": "2024-01-20T10:00:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "size": 10,
                "pages": 1
            }
    """
    return await list_user_autopays(
        db,
        current_user_id=current_user.user_id,
        phone_number=phone_number,
        page=page,
        size=size,
        status=status,
        tag=tag,
        sort=sort,
    )


@router.get("/autopay_credentials", response_model=AutoPayCredentialOut)
async def get_autopay_credentials(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"])
):
    """Fetch the stored autopay payment credentials for the authenticated user."""
    return await fetch_user_autopay_credentials(db, user_id=current_user.user_id)


@router.put("/autopay_credentials", response_model=AutoPayCredentialOut)
async def put_autopay_credentials(
    payload: AutoPayCredentialUpsert,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"])
):
    """Replace the user's autopay payment credentials with the provided payload."""
    return await replace_user_autopay_credentials(
        db,
        user_id=current_user.user_id,
        obj_in=payload,
    )


@router.patch("/{autopay_id}", response_model=AutoPayOut)
async def edit_autopay(
    autopay_id: int,
    payload: AutoPayUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"])
):
    """
    Update an existing autopay rule.
    
    Modify autopay settings such as frequency, next due date, status, or tags.
    Allows users to adjust their recurring recharge schedule without deleting
    and recreating the rule. Changes take effect immediately.
    
    Security:
        - Requires valid JWT access token
        - Scope: User
        - Users can only update their own autopay rules
    
    Path Parameters:
        - autopay_id (int): ID of autopay to update (must belong to current user)
    
    Request Body:
        AutoPayUpdate (JSON) - all fields optional:
            - frequency (str): New recurrence pattern (daily, weekly, monthly, etc.)
            - next_due_date (datetime): Reschedule next execution
            - status (str): New status (active, paused, completed)
            - tag (str): Update organization tag
            - notes (str): Update user notes
    
    Returns:
        AutoPayOut: Updated autopay object with all current details
    
    Raises:
        HTTPException(400): Invalid update data or validation error
        HTTPException(401): User not authenticated
        HTTPException(403): Autopay does not belong to current user
        HTTPException(404): Autopay not found
    
    Example:
        Request:
            PATCH /autopay/12
            Headers: Authorization: Bearer <jwt_token>
            Body:
            {
                "frequency": "weekly",
                "next_due_date": "2024-01-29T10:00:00Z",
                "status": "paused"
            }
        
        Response (200 OK):
            {
                "autopay_id": 12,
                "user_id": 42,
                "plan_id": 5,
                "phone_number": "+919876543210",
                "frequency": "weekly",
                "next_due_date": "2024-01-29T10:00:00Z",
                "status": "paused",
                "tag": "work",
                "created_at": "2024-01-20T10:00:00Z",
                "updated_at": "2024-01-20T11:00:00Z"
            }
    """
    return await update_user_autopay(
        db, autopay_id=autopay_id, obj_in=payload, current_user_id=current_user.user_id
    )


@router.delete("/{autopay_id}", status_code=204)
async def remove_autopay(
    autopay_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"])
):
    """
    Delete an autopay rule.
    
    Removes an autopay rule permanently. If the autopay was scheduled for
    execution, it will not be processed. This action cannot be undone;
    users must create a new autopay to resume auto-recharges.
    
    Security:
        - Requires valid JWT access token
        - Scope: User
        - Users can only delete their own autopay rules
    
    Path Parameters:
        - autopay_id (int): ID of autopay to delete (must belong to current user)
    
    Returns:
        None: HTTP 204 No Content (successful deletion)
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Autopay does not belong to current user
        HTTPException(404): Autopay not found
    
    Example:
        Request:
            DELETE /autopay/12
            Headers: Authorization: Bearer <jwt_token>
        
        Response (204 No Content):
            (empty body)
    """
    await delete_user_autopay(db, autopay_id=autopay_id, current_user_id=current_user.user_id)
    return None


# ====================== ADMIN ENDPOINTS ======================
@router.get("/admin/all", response_model=PaginatedAutoPayAdmin)
async def admin_list_all(
    page: int = Query(0, ge=0),
    size: int = Query(0, ge=0, le=100),
    status: AutoPayStatus | None = None,
    tag: AutoPayTag | None = None,
    phone_number: str | None = None,
    sort: Literal[
        "created_at_desc",
        "created_at_asc",
        "next_due_date_desc",
        "next_due_date_asc",
    ] = "created_at_desc",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Autopay:read"])
):
    """
    List all autopay rules in the system (Admin view).
    
    Retrieves paginated list of all autopay rules across all users. Used by
    admins to monitor autopay activity, troubleshoot issues, and analyze usage
    patterns. Supports filtering and sorting for analytics.
    
    Security:
        - Requires valid JWT access token
        - Scope: Autopay:read
        - Typically restricted to admin/support team
    
    Query Parameters:
        - page (int, optional): Page number (default: 1, minimum: 1)
        - size (int, optional): Records per page (default: 20, max: 100)
        - status (str, optional): Filter by status (active, paused, completed)
        - phone_number (str, optional): Filter by phone number (partial match)
        - tag (str, optional): Filter by tag (exact match)
        - sort (str, optional): Sorting order (default: created_at_desc):
            - created_at_desc: Most recently created first
            - created_at_asc: Oldest first
            - next_due_date_desc: Due later first
            - next_due_date_asc: Due sooner first
    
    Returns:
        PaginatedAutoPay:
            - items (list): Array of AutoPayOut objects with all details
            - total (int): Total count of autopay rules in system
            - page (int): Current page number
            - size (int): Records per page
            - pages (int): Total pages
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Autopay:read scope
        HTTPException(400): Invalid pagination or filter parameters
    
    Example:
        Request:
            GET /autopay/admin/all?page=1&size=50&status=active&sort=next_due_date_asc
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            {
                "items": [
                    {
                        "autopay_id": 12,
                        "user_id": 42,
                        "plan_id": 5,
                        "phone_number": "+919876543210",
                        "frequency": "monthly",
                        "next_due_date": "2024-02-20T10:00:00Z",
                        "status": "active",
                        "tag": "work",
                        "created_at": "2024-01-20T10:00:00Z"
                    }
                ],
                "total": 156,
                "page": 1,
                "size": 50,
                "pages": 4
            }
    """
    return await list_all_autopays(
        db, page=page, size=size, status=status, tag=tag, sort=sort, phone_number=phone_number
    )


@router.post("/admin/process-due", response_model=list[dict])
async def admin_process_due(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Autopay:write"])
):
    """
    Manually trigger processing of all due autopay rules.
    
    Executes all active autopay rules whose next_due_date <= current time.
    This endpoint is typically called by scheduled jobs (cron) to process
    autopays at regular intervals. Returns status for each autopay attempt.
    
    Normally called via automated scheduler, but can be triggered manually
    for troubleshooting or batch operations.
    
    Security:
        - Requires valid JWT access token
        - Scope: Autopay:write
        - Restricted to admin/operations team only
    
    Returns:
        list[dict]: Array of processing results, each containing:
            - autopay_id (int): Processed autopay ID
            - status (str): Result (success, failed, skipped)
            - reason (str, optional): Reason for failure if applicable
            - processed_at (datetime): When this autopay was processed
            - next_due_date (datetime): Updated next due date
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Autopay:write scope
        HTTPException(500): Batch processing error
    
    Example:
        Request:
            POST /autopay/admin/process-due
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            [
                {
                    "autopay_id": 12,
                    "status": "success",
                    "processed_at": "2024-01-20T10:05:00Z",
                    "next_due_date": "2024-02-20T10:00:00Z"
                },
                {
                    "autopay_id": 15,
                    "status": "failed",
                    "reason": "Insufficient wallet balance",
                    "processed_at": "2024-01-20T10:05:00Z"
                },
                {
                    "autopay_id": 18,
                    "status": "success",
                    "processed_at": "2024-01-20T10:05:00Z",
                    "next_due_date": "2024-02-25T10:00:00Z"
                }
            ]
    """
    return await process_due_autopays(db)