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
    authorized = Security(require_scopes, scopes=["PlanGroups:write"], use_cache=False)
):
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
    filters: PlanGroupFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["PlanGroups:read"], use_cache=False)
):
    query = select(PlanGroup)
    if filters.search:
        query = query.where(PlanGroup.group_name.ilike(f"%{filters.search}%"))
    valid_order_fields = {"group_id", "group_name"}
    if filters.order_by not in valid_order_fields:
        raise HTTPException(status_code=400, detail="Invalid order_by field")
    order_column = getattr(PlanGroup, filters.order_by)
    query = query.order_by(asc(order_column) if filters.order_dir == "asc" else desc(order_column))
    offset = (filters.page - 1) * filters.limit
    query = query.offset(offset).limit(filters.limit)
    result = await db.execute(query)
    groups = result.scalars().all()
    return groups

# READ one PlanGroup by ID
@router.get("/plan-group/{group_id}", response_model=PlanGroupResponse)
async def get_plan_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["PlanGroups:read"], use_cache=False)
):
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
    authorized = Security(require_scopes, scopes=["PlanGroups:edit"], use_cache=False)
):
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
    authorized = Security(require_scopes, scopes=["PlanGroups:delete"], use_cache=False)
):
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
    authorized = Security(require_scopes, scopes=["Plans:write"], use_cache=False)
):
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
    authorized = Security(require_scopes, scopes=["Plans:edit"], use_cache=False)
):
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
    authorized = Security(require_scopes, scopes=["Plans:delete"], use_cache=False)
):
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
    authorized = Security(require_scopes, scopes=["Plans:read"], use_cache=False)
):
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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Plans:read"], use_cache=False)
):
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
    query = select(Plan).where(Plan.status == "active")

    if filters.search:
        query = query.where(Plan.plan_name.ilike(f"%{filters.search}%"))
    if filters.type:
        query = query.where(Plan.plan_type == filters.type)

    order_column = getattr(Plan, filters.order_by, Plan.plan_id)
    query = query.order_by(asc(order_column) if filters.order_dir == "asc" else desc(order_column))
    offset = (filters.page - 1) * filters.limit
    query = query.offset(offset).limit(filters.limit)

    result = await db.execute(query)
    plans = result.scalars().all()
    return plans
