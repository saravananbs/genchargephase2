from sqlalchemy import select, asc, desc, and_
from sqlalchemy.orm import joinedload
from typing import List, Optional, Tuple
from ..models.admins import Admin
from ..models.roles import Role
from ..models.autopay import AutoPay
from ..models.plans import Plan
from ..models.users import User
from ..models.backup import Backup
from ..models.current_active_plans import CurrentActivePlan
from ..schemas.reports import AdminReportFilter, AutoPayReportFilter, BackupReportFilter, CurrentActivePlansFilter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, asc, desc, join, cast, Float


async def get_admin_report(
    session: AsyncSession, filters: AdminReportFilter
) -> List[Admin]:

    query = select(Admin).options(joinedload(Admin.role))

    conditions = []

    # Filter by role names
    if filters.roles and len(filters.roles) > 0:
        query = query.join(Role)
        conditions.append(Role.role_name.in_(filters.roles))

    # Created date range
    if filters.created_from and filters.created_to:
        conditions.append(
            and_(Admin.created_at >= filters.created_from, Admin.created_at <= filters.created_to)
        )

    # Updated date range
    if filters.updated_from and filters.updated_to:
        conditions.append(
            and_(Admin.updated_at >= filters.updated_from, Admin.updated_at <= filters.updated_to)
        )

    if conditions:
        query = query.where(and_(*conditions))

    # Ordering
    order_column = getattr(Admin, filters.order_by)
    query = query.order_by(asc(order_column) if filters.order_dir == "asc" else desc(order_column))

    # Pagination (skip if limit or offset = 0)
    if filters.limit > 0:
        query = query.limit(filters.limit)
    if filters.offset > 0:
        query = query.offset(filters.offset)

    result = await session.execute(query)
    return result.scalars().all()


async def get_autopays(
    session: AsyncSession,
    filters: AutoPayReportFilter
) -> List[AutoPay]:
    """
    Returns list of AutoPay ORM objects (with joined plan and user) matching the filters.
    Pagination is applied only when limit>0 and offset>0 (as requested).
    """
    # base query selecting AutoPay and joined relationships
    stmt = select(AutoPay).options(
        joinedload(AutoPay.plan),
        joinedload(AutoPay.user)
    )

    conditions = []

    # status & tag filters (stored as strings in your model)
    if filters.statuses:
        conditions.append(AutoPay.status.in_(filters.statuses))
    if filters.tags:
        conditions.append(AutoPay.tag.in_(filters.tags))

    # plan & user filters
    if filters.plan_ids:
        conditions.append(AutoPay.plan_id.in_(filters.plan_ids))
    if filters.user_ids:
        conditions.append(AutoPay.user_id.in_(filters.user_ids))
    if filters.phone_numbers:
        conditions.append(AutoPay.phone_number.in_(filters.phone_numbers))

    # next_due and created date ranges
    if filters.next_due_from and filters.next_due_to:
        conditions.append(
            and_(AutoPay.next_due_date >= filters.next_due_from, AutoPay.next_due_date <= filters.next_due_to)
        )
    elif filters.next_due_from:
        conditions.append(AutoPay.next_due_date >= filters.next_due_from)
    elif filters.next_due_to:
        conditions.append(AutoPay.next_due_date <= filters.next_due_to)

    if filters.created_from and filters.created_to:
        conditions.append(
            and_(AutoPay.created_at >= filters.created_from, AutoPay.created_at <= filters.created_to)
        )
    elif filters.created_from:
        conditions.append(AutoPay.created_at >= filters.created_from)
    elif filters.created_to:
        conditions.append(AutoPay.created_at <= filters.created_to)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    # ordering: allow ordering by related fields (plan.price -> use join and attribute)
    order_col = None
    # direct autopay columns
    if filters.order_by in {"autopay_id", "next_due_date", "created_at"}:
        order_col = getattr(AutoPay, filters.order_by)
    elif filters.order_by == "price":
        # join to Plan and order by Plan.price
        stmt = stmt.join(Plan, AutoPay.plan)
        order_col = Plan.price
    elif filters.order_by == "plan_name":
        stmt = stmt.join(Plan, AutoPay.plan)
        order_col = Plan.plan_name
    else:
        order_col = AutoPay.created_at

    stmt = stmt.order_by(asc(order_col) if filters.order_dir == "asc" else desc(order_col))

    # Pagination: apply only if limit>0 or offset>0 as per user requirement:
    # Interpreting requirement: "if limit or offset is zero then no need of pagination right"
    # We'll treat pagination applied only when both limit>0 AND offset>=0 – but to be safe:
    if (filters.limit and filters.limit > 0) and (filters.offset is not None):
        # If offset == 0 but limit>0, we still apply pagination because user asked for limit
        stmt = stmt.limit(filters.limit)
        if filters.offset > 0:
            stmt = stmt.offset(filters.offset)

    result = await session.execute(stmt)
    return result.scalars().unique().all()


async def get_backups(session: AsyncSession, filters: BackupReportFilter) -> List[Backup]:
    query = select(Backup)
    conditions = []

    # Filters
    if filters.backup_data:
        conditions.append(Backup.backup_data.in_(filters.backup_data))

    if filters.backup_status:
        conditions.append(Backup.backup_status.in_(filters.backup_status))

    if filters.created_from and filters.created_to:
        conditions.append(and_(Backup.created_at >= filters.created_from, Backup.created_at <= filters.created_to))
    elif filters.created_from:
        conditions.append(Backup.created_at >= filters.created_from)
    elif filters.created_to:
        conditions.append(Backup.created_at <= filters.created_to)

    if filters.created_by:
        conditions.append(Backup.created_by.in_(filters.created_by))

    if filters.min_size_mb and filters.max_size_mb:
        conditions.append(and_(cast(Backup.size_mb, Float) >= filters.min_size_mb,
                               cast(Backup.size_mb, Float) <= filters.max_size_mb))
    elif filters.min_size_mb:
        conditions.append(cast(Backup.size_mb, Float) >= filters.min_size_mb)
    elif filters.max_size_mb:
        conditions.append(cast(Backup.size_mb, Float) <= filters.max_size_mb)

    if conditions:
        query = query.where(and_(*conditions))

    # Ordering
    order_col = getattr(Backup, filters.order_by)
    query = query.order_by(asc(order_col) if filters.order_dir == "asc" else desc(order_col))

    # Pagination
    if filters.limit > 0:
        query = query.limit(filters.limit)
    if filters.offset > 0:
        query = query.offset(filters.offset)

    result = await session.execute(query)
    return result.scalars().unique().all()


async def get_current_active_plans(
    session: AsyncSession,
    filters: CurrentActivePlansFilter
) -> List[CurrentActivePlan]:
    """
    Return list of CurrentActivePlan ORM objects joined with Plan and User.
    Pagination is applied only when both limit>0 AND offset>0 (skip otherwise).
    """
    stmt = select(CurrentActivePlan).options(
        joinedload(CurrentActivePlan.plan),
        joinedload(CurrentActivePlan.user)
    )

    conditions = []

    # Simple equality/filter lists
    if filters.ids:
        conditions.append(CurrentActivePlan.id.in_(filters.ids))
    if filters.user_ids:
        conditions.append(CurrentActivePlan.user_id.in_(filters.user_ids))
    if filters.plan_ids:
        conditions.append(CurrentActivePlan.plan_id.in_(filters.plan_ids))
    if filters.phone_numbers:
        conditions.append(CurrentActivePlan.phone_number.in_(filters.phone_numbers))
    if filters.statuses:
        conditions.append(CurrentActivePlan.status.in_(filters.statuses))

    # Plan-related filters require join when filtering on plan columns
    if filters.plan_types or filters.plan_statuses:
        stmt = stmt.join(Plan, CurrentActivePlan.plan)
        if filters.plan_types:
            conditions.append(Plan.plan_type.in_(filters.plan_types))
        if filters.plan_statuses:
            conditions.append(Plan.status.in_(filters.plan_statuses))

    # valid_from range
    if filters.valid_from_from and filters.valid_from_to:
        conditions.append(and_(CurrentActivePlan.valid_from >= filters.valid_from_from,
                               CurrentActivePlan.valid_from <= filters.valid_from_to))
    elif filters.valid_from_from:
        conditions.append(CurrentActivePlan.valid_from >= filters.valid_from_from)
    elif filters.valid_from_to:
        conditions.append(CurrentActivePlan.valid_from <= filters.valid_from_to)

    # valid_to range
    if filters.valid_to_from and filters.valid_to_to:
        conditions.append(and_(CurrentActivePlan.valid_to >= filters.valid_to_from,
                               CurrentActivePlan.valid_to <= filters.valid_to_to))
    elif filters.valid_to_from:
        conditions.append(CurrentActivePlan.valid_to >= filters.valid_to_from)
    elif filters.valid_to_to:
        conditions.append(CurrentActivePlan.valid_to <= filters.valid_to_to)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    # Ordering - support related fields by joining Plan or User as needed
    order_col = None
    if filters.order_by in {"id", "user_id", "plan_id", "phone_number", "valid_from", "valid_to", "status"}:
        order_col = getattr(CurrentActivePlan, filters.order_by)
    elif filters.order_by in {"plan_name", "plan_price", "plan_type"}:
        # ensure joined with Plan
        if "plan" not in [j.entity for j in stmt._setup_joins or []]:  # can't rely on internals—safe to join again
            stmt = stmt.join(Plan, CurrentActivePlan.plan)
        if filters.order_by == "plan_name":
            order_col = Plan.plan_name
        elif filters.order_by == "plan_price":
            order_col = Plan.price
        else:
            order_col = Plan.plan_type
    elif filters.order_by == "user_name":
        # join user
        stmt = stmt.join(User, CurrentActivePlan.user)
        order_col = User.name
    else:
        order_col = CurrentActivePlan.valid_to

    stmt = stmt.order_by(asc(order_col) if filters.order_dir == "asc" else desc(order_col))

    # Pagination: apply only when both limit>0 AND offset>0 (skip otherwise)
    if (filters.limit is not None and filters.offset is not None) and (filters.limit > 0 and filters.offset > 0):
        stmt = stmt.limit(filters.limit).offset(filters.offset)

    result = await session.execute(stmt)
    # scalars().unique() to avoid duplicates from joins
    return result.scalars().unique().all()
