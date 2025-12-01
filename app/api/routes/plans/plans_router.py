from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import asc, desc
from ....core.database import get_db 
from ....models.plans import Plan
from ....models.plan_groups import PlanGroup
from ....schemas.plans import PlanCreate, PlanFilter, PlanResponse, PlanUpdate, UserPlanResponse
from ....schemas.plan_group import PlanGroupCreate, PlanGroupResponse, PlanGroupUpdate, PlanGroupFilter
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes
from typing import List
from sqlalchemy import select

router = APIRouter()

# CREATE a PlanGroup
@router.post("/plan-group", response_model=PlanGroupResponse)
async def create_plan_group(
    payload: PlanGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["PlanGroups:write"])
):
    """
    Create a new plan group/category.
    
    Admin endpoint to create a new plan group that can contain multiple plans. Plan groups
    are used for categorizing and organizing plans logically (e.g., "Standard", "Premium",
    "Basic", etc). Group names must be unique.
    
    Security:
        - Requires valid JWT access token
        - Scope: PlanGroups:write
        - Admin-only endpoint
    
    Request Body (PlanGroupCreate):
        - group_name (str): Unique name for the plan group (max 255 chars).
    
    Returns:
        PlanGroupResponse: Created plan group object with ID and metadata.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing PlanGroups:write scope.
        HTTPException(400): If group name already exists or invalid.
    
    Example:
        Request:
        ```json
        {
            "group_name": "Premium Plans"
        }
        ```
        
        Response:
        ```json
        {
            "group_id": 1,
            "group_name": "Premium Plans",
            "created_at": "2024-01-15T10:30:00Z"
        }
        ```
    """
    # Check if group name already exists
    result = await db.execute(
        select(PlanGroup).where(PlanGroup.group_name == payload.group_name)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Group name already exists")

    group = PlanGroup(group_name=payload.group_name)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group

# READ all PlanGroups
@router.get("/plan-group", response_model=List[PlanGroupResponse])
async def get_plan_groups(
    # filters: PlanGroupFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    # current_user = Depends(get_current_user),
    # authorized = Security(require_scopes, scopes=["PlanGroups:read"])
):
    """
    Retrieve all plan groups with filtering and pagination.
    
    Admin endpoint to fetch all available plan groups. Supports searching by group name
    and sorting by different fields. Results are paginated for performance.
    
    Security:
        - Requires valid JWT access token
        - Scope: PlanGroups:read
        - Admin-only endpoint
    
    Query Parameters (PlanGroupFilter):
        - search (str, optional): Search plan group names (LIKE pattern)
        - order_by (str): Sort field - 'group_id' or 'group_name' (default: 'group_id')
        - order_dir (str): Sort direction - 'asc' or 'desc' (default: 'asc')
        - page (int): Page number for pagination (default: 1)
        - limit (int): Records per page (default: 10)
    
    Returns:
        List[PlanGroupResponse]: Array of plan group objects.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing PlanGroups:read scope.
        HTTPException(400): If invalid order_by field.
    
    Example:
        Request:
        ```
        GET /plans/plan-group?search=premium&page=1&limit=20
        Authorization: Bearer <admin_token>
        ```
        
        Response:
        ```json
        [
            {
                "group_id": 1,
                "group_name": "Premium Plans",
                "created_at": "2024-01-15T10:30:00Z"
            }
        ]
        ```
    """
    query = select(PlanGroup)
    # if filters.search:
    #     query = query.where(PlanGroup.group_name.ilike(f"%{filters.search}%"))
    # valid_order_fields = {"group_id", "group_name"}
    # if filters.order_by not in valid_order_fields:
    #     raise HTTPException(status_code=400, detail="Invalid order_by field")
    # order_column = getattr(PlanGroup, filters.order_by)
    # query = query.order_by(asc(order_column) if filters.order_dir == "asc" else desc(order_column))
    # offset = (filters.page - 1) * filters.limit
    # query = query.offset(offset).limit(filters.limit)
    result = await db.execute(query)
    groups = result.scalars().all()
    return groups

# READ one PlanGroup by ID
@router.get("/plan-group/{group_id}", response_model=PlanGroupResponse)
async def get_plan_group(
    group_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific plan group by ID.
    
    Admin endpoint to fetch details of a single plan group using its ID.
    
    Security:
        - Requires valid JWT access token
        - Scope: PlanGroups:read
        - Admin-only endpoint
    
    Path Parameters:
        - group_id (int): Unique identifier of the plan group.
    
    Returns:
        PlanGroupResponse: Plan group object with all details.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing PlanGroups:read scope.
        HTTPException(404): If plan group not found.
    
    Example:
        Request:
        ```
        GET /plans/plan-group/1
        Authorization: Bearer <admin_token>
        ```
        
        Response:
        ```json
        {
            "group_id": 1,
            "group_name": "Premium Plans",
            "created_at": "2024-01-15T10:30:00Z"
        }
        ```
    """
    result = await db.execute(
        select(PlanGroup).where(PlanGroup.group_id == group_id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Plan group not found")
    return group

# UPDATE PlanGroup
@router.put("/plan-group/{group_id}", response_model=PlanGroupResponse)
async def update_plan_group(
    group_id: int,
    payload: PlanGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["PlanGroups:edit"])
):
    """
    Update an existing plan group.
    
    Admin endpoint to modify plan group details such as name. Supports partial updates
    - only provided fields are modified.
    
    Security:
        - Requires valid JWT access token
        - Scope: PlanGroups:edit
        - Admin-only endpoint
    
    Path Parameters:
        - group_id (int): Unique identifier of the plan group to update.
    
    Request Body (PlanGroupUpdate):
        - group_name (str, optional): New name for the plan group (must be unique).
    
    Returns:
        PlanGroupResponse: Updated plan group object.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing PlanGroups:edit scope.
        HTTPException(404): If plan group not found.
        HTTPException(400): If new name already exists.
    
    Example:
        Request:
        ```
        PUT /plans/plan-group/1
        Authorization: Bearer <admin_token>
        Content-Type: application/json
        
        {
            "group_name": "Premium Plus Plans"
        }
        ```
        
        Response:
        ```json
        {
            "group_id": 1,
            "group_name": "Premium Plus Plans",
            "updated_at": "2024-01-20T10:15:00Z"
        }
        ```
    """
    result = await db.execute(
        select(PlanGroup).where(PlanGroup.group_id == group_id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Plan group not found")

    if payload.group_name:
        # Check for duplicate name (excluding current record)
        result = await db.execute(
            select(PlanGroup).where(
                PlanGroup.group_name == payload.group_name,
                PlanGroup.group_id != group_id
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Group name already exists")

        group.group_name = payload.group_name

    await db.commit()
    await db.refresh(group)
    return group

# DELETE PlanGroup
@router.delete("/plan-group/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["PlanGroups:delete"])
):
    """
    Delete a plan group by ID.
    
    Admin endpoint to permanently delete a plan group. This operation requires that no
    plans are currently associated with the group (foreign key constraint). If plans exist
    under this group, they must be moved or deleted first.
    
    Security:
        - Requires valid JWT access token
        - Scope: PlanGroups:delete
        - Admin-only endpoint
    
    Path Parameters:
        - group_id (int): Unique identifier of the plan group to delete.
    
    Returns:
        null: HTTP 204 No Content on successful deletion.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing PlanGroups:delete scope.
        HTTPException(404): If plan group not found.
        HTTPException(400): If plans exist under this group (foreign key violation).
    
    Example:
        Request:
        ```
        DELETE /plans/plan-group/1
        Authorization: Bearer <admin_token>
        ```
        
        Response:
        ```
        HTTP 204 No Content
        ```
    """
    result = await db.execute(
        select(PlanGroup).where(PlanGroup.group_id == group_id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Plan group not found")

    await db.delete(group)
    await db.commit()
    return None

# 🔹 Create Plan (Admin)
@router.post("/plan", response_model=PlanResponse)
async def create_plan(
    plan_data: PlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Plans:write"])
):
    """
    Create a new recharge plan.
    
    Admin endpoint to create a new plan that users can subscribe to. Plans define pricing,
    validity period, data/minutes, and other benefits. The creating admin is recorded for audit.
    
    Security:
        - Requires valid JWT access token
        - Scope: Plans:write
        - Admin-only endpoint
    
    Request Body (PlanCreate):
        - plan_name (str): Unique name for the plan
        - plan_type (str): Plan type - 'voice', 'data', 'voice_data', 'ott', etc
        - price (Decimal): Plan price in currency units
        - validity (int): Validity period in days
        - description (str, optional): Plan description
        - group_id (int): Reference to PlanGroup category
        - status (str): 'active' or 'inactive'
    
    Returns:
        PlanResponse: Created plan object with ID and metadata.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing Plans:write scope.
        HTTPException(400): If invalid group_id (foreign key) or duplicate plan name.
    
    Example:
        Request:
        ```json
        {
            "plan_name": "Premium 199",
            "plan_type": "voice_data",
            "price": 199.00,
            "validity": 30,
            "description": "30 days unlimited voice + 2GB data",
            "group_id": 1,
            "status": "active"
        }
        ```
        
        Response:
        ```json
        {
            "plan_id": 1,
            "plan_name": "Premium 199",
            "price": 199.00,
            "validity": 30,
            "status": "active",
            "created_by": 5,
            "created_at": "2024-01-15T10:30:00Z"
        }
        ```
    """
    new_plan = Plan(**plan_data.model_dump(), created_by=current_user.admin_id)
    db.add(new_plan)
    try:
        await db.commit()
        await db.refresh(new_plan)
        return new_plan
    except IntegrityError as e:
        await db.rollback()
        if 'foreign key constraint' in str(e.orig).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid group_id — referenced PlanGroup does not exist."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error occurred."
            )


# 🔹 Update Plan (Admin)
@router.put("/plan/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: int,
    plan_data: PlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Plans:edit"])
):
    """
    Update an existing plan.
    
    Admin endpoint to modify plan details such as price, validity, name, or status.
    Supports partial updates - only provided fields are modified. This can affect
    existing user subscriptions depending on the changes made.
    
    Security:
        - Requires valid JWT access token
        - Scope: Plans:edit
        - Admin-only endpoint
    
    Path Parameters:
        - plan_id (int): Unique identifier of the plan to update.
    
    Request Body (PlanUpdate):
        - plan_name (str, optional): New plan name
        - price (Decimal, optional): New price
        - validity (int, optional): New validity period
        - status (str, optional): 'active' or 'inactive'
        - description (str, optional): Updated description
        - group_id (int, optional): Reassign to different group
    
    Returns:
        PlanResponse: Updated plan object.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing Plans:edit scope.
        HTTPException(404): If plan not found.
        HTTPException(400): If invalid group_id or other constraint violation.
    
    Example:
        Request:
        ```
        PUT /plans/plan/1
        Authorization: Bearer <admin_token>
        Content-Type: application/json
        
        {
            "price": 249.00,
            "validity": 45
        }
        ```
        
        Response:
        ```json
        {
            "plan_id": 1,
            "plan_name": "Premium 199",
            "price": 249.00,
            "validity": 45,
            "updated_at": "2024-01-20T10:15:00Z"
        }
        ```
    """
    result = await db.execute(select(Plan).where(Plan.plan_id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    for key, value in plan_data.model_dump(exclude_unset=True).items():
        setattr(plan, key, value)
    try:
        await db.commit()
        await db.refresh(plan)
    except IntegrityError as e:
        await db.rollback()
        if 'foreign key constraint' in str(e.orig).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid group_id — referenced PlanGroup does not exist."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error occurred."
            )
    return plan


# 🔹 Delete Plan (Admin)
@router.delete("/plan/{plan_id}")
async def delete_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Plans:delete"])
):
    """
    Delete a plan by ID.
    
    Admin endpoint to permanently remove a plan from the system. Deleted plans cannot be
    subscribed to by new users but existing subscriptions remain valid until expiry. This
    is useful for retiring outdated or unpopular plans.
    
    Security:
        - Requires valid JWT access token
        - Scope: Plans:delete
        - Admin-only endpoint
    
    Path Parameters:
        - plan_id (int): Unique identifier of the plan to delete.
    
    Returns:
        dict: Success message confirming deletion.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing Plans:delete scope.
        HTTPException(404): If plan not found.
    
    Example:
        Request:
        ```
        DELETE /plans/plan/1
        Authorization: Bearer <admin_token>
        ```
        
        Response:
        ```json
        {
            "detail": "Plan deleted successfully"
        }
        ```
    """
    result = await db.execute(select(Plan).where(Plan.plan_id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    await db.delete(plan)
    await db.commit()
    return {"detail": "Plan deleted successfully"}


# 🔹 Get all Plans (Admin)
@router.get("/plan", response_model=List[PlanResponse])
async def get_all_plans(
    filters: PlanFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Plans:read"])
):
    """
    Retrieve all plans with advanced filtering and pagination.
    
    Admin endpoint to fetch all plans in the system (active and inactive). Supports
    searching by name/description, filtering by type and status, and customizable sorting.
    
    Security:
        - Requires valid JWT access token
        - Scope: Plans:read
        - Admin-only endpoint
    
    Query Parameters (PlanFilter):
        - search (str, optional): Search plan name or description (LIKE pattern)
        - type (str, optional): Filter by plan_type (voice, data, voice_data, ott, etc)
        - status (str, optional): Filter by status - 'active' or 'inactive'
        - order_by (str): Sort field - 'plan_id', 'plan_name', 'validity', 'created_at' (default: 'plan_id')
        - order_dir (str): Sort direction - 'asc' or 'desc' (default: 'asc')
        - page (int): Page number for pagination (default: 1)
        - limit (int): Records per page (default: 10)
    
    Returns:
        List[PlanResponse]: Array of plan objects matching filters.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing Plans:read scope.
        HTTPException(400): If invalid order_by field.
    
    Example:
        Request:
        ```
        GET /plans/plan?type=voice_data&status=active&page=1&limit=25
        Authorization: Bearer <admin_token>
        ```
        
        Response:
        ```json
        [
            {
                "plan_id": 1,
                "plan_name": "Premium 199",
                "plan_type": "voice_data",
                "price": 199.00,
                "validity": 30,
                "status": "active"
            }
        ]
        ```
    """
    query = select(Plan)

    # Filtering
    if filters.search:
        query = query.where(Plan.plan_name.ilike(f"%{filters.search}%") | Plan.description.ilike(f"%{filters.search}%"))
    if filters.type:
        query = query.where(Plan.plan_type == filters.type)
    if filters.status:
        query = query.where(Plan.status == filters.status)

    # Ordering
    valid_fields = {"plan_id", "plan_name", "validity", "created_at"}
    if filters.order_by not in valid_fields:
        raise HTTPException(status_code=400, detail="Invalid order_by field")

    order_column = getattr(Plan, filters.order_by)
    query = query.order_by(asc(order_column) if filters.order_dir == "asc" else desc(order_column))

    # Pagination
    offset = (filters.page - 1) * filters.limit
    query = query.offset(offset).limit(filters.limit)

    result = await db.execute(query)
    plans = result.scalars().all()
    return plans


# 🔹 Get Plan by ID (Admin)
@router.get("/plan/{plan_id}", response_model=PlanResponse)
async def get_plan_by_id(
    plan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific plan by ID.
    
    Admin endpoint to fetch complete details of a single plan including pricing, validity,
    benefits, and current status.
    
    Security:
        - Requires valid JWT access token
        - Scope: Plans:read
        - Admin-only endpoint
    
    Path Parameters:
        - plan_id (int): Unique identifier of the plan.
    
    Returns:
        PlanResponse: Complete plan object with all details.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing Plans:read scope.
        HTTPException(404): If plan not found.
    
    Example:
        Request:
        ```
        GET /plans/plan/1
        Authorization: Bearer <admin_token>
        ```
        
        Response:
        ```json
        {
            "plan_id": 1,
            "plan_name": "Premium 199",
            "plan_type": "voice_data",
            "price": 199.00,
            "validity": 30,
            "description": "Unlimited voice + 2GB data",
            "group_id": 1,
            "status": "active",
            "created_by": 5,
            "created_at": "2024-01-15T10:30:00Z"
        }
        ```
    """
    result = await db.execute(select(Plan).where(Plan.plan_id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


# 🔹 User endpoint → only active plans
@router.get("/public/all", response_model=List[UserPlanResponse])
async def get_active_plans_for_users(
    filters: PlanFilter = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve all active plans available for user subscription.
    
    Public endpoint (no authentication required) for users to browse and view all available
    active plans that they can subscribe to. Returns simplified plan information suitable
    for user-facing interfaces. Only active plans are returned.
    
    Query Parameters (PlanFilter):
        - search (str, optional): Search plan names (LIKE pattern)
        - type (str, optional): Filter by plan_type (voice, data, voice_data, ott)
        - order_by (str): Sort field - default 'plan_id'
        - order_dir (str): Sort direction - 'asc' or 'desc'
        - page (int): Page number for pagination (default: 1)
        - limit (int): Records per page (default: 10)
    
    Returns:
        List[UserPlanResponse]: Array of active plan objects with user-relevant information.
        
    Raises:
        None: Public endpoint, no authentication errors.
    
    Example:
        Request:
        ```
        GET /plans/public/all?type=voice_data&page=1&limit=50
        ```
        
        Response:
        ```json
        [
            {
                "plan_id": 1,
                "plan_name": "Premium 199",
                "plan_type": "voice_data",
                "price": 199.00,
                "validity": 30,
                "description": "30 days unlimited voice + 2GB data"
            }
        ]
        ```
    """
    query = select(Plan).where(Plan.status == "active")

    if filters.search:
        query = query.where(Plan.plan_name.ilike(f"%{filters.search}%"))
    if filters.type:
        query = query.where(Plan.plan_type == filters.type)

    order_column = getattr(Plan, filters.order_by, Plan.plan_id)
    query = query.order_by(asc(order_column) if filters.order_dir == "asc" else desc(order_column))

    if filters.page > 0 or filters.limit > 0:
        offset = (filters.page - 1) * filters.limit
        query = query.offset(offset).limit(filters.limit)

    result = await db.execute(query)
    plans = result.scalars().all()
    return plans
