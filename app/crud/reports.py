from sqlalchemy import select, asc, desc, and_, func
from sqlalchemy.orm import joinedload
from typing import List, Optional, Tuple
from ..utils.content import make_naive
from ..models.admins import Admin
from ..models.roles import Role
from ..models.autopay import AutoPay
from ..models.plan_groups import PlanGroup
from ..models.plans import Plan
from ..models.users import User
from ..models.backup import Backup
from ..models.offer_types import OfferType
from ..models.referral import ReferralReward
from ..models.offers import Offer
from ..models.current_active_plans import CurrentActivePlan
from ..models.roles_permissions import RolePermission
from ..models.sessions import Session
from ..models.roles import Role
from ..models.permissions import Permission
from ..models.transactions import Transaction
from ..models.users_archieve import UserArchieve
from ..models.users import User
from ..schemas.reports import (
    AdminReportFilter, AutoPayReportFilter, BackupReportFilter, CurrentActivePlansFilter,
    OfferReportFilter, PlanReportFilter, ReferralReportFilter, RolePermissionReportFilter,
    SessionsReportFilter, TransactionsReportFilter, UsersArchiveFilter, UsersReportFilter
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, asc, desc, join, cast, Float


async def get_admin_report(
    session: AsyncSession, filters: AdminReportFilter
) -> List[Admin]:
    """
    Retrieve a list of admin users matching the provided filters.

    Args:
        session (AsyncSession): Async database session.
        filters (AdminReportFilter): Filtering, ordering and pagination parameters.

    Returns:
        List[Admin]: Matching Admin ORM objects with related Role loaded.
    """
    query = select(Admin).options(joinedload(Admin.role))

    conditions = []

    filters.created_from = make_naive(filters.created_from)
    filters.created_to = make_naive(filters.created_to)
    filters.updated_from = make_naive(filters.updated_from)
    filters.updated_to = make_naive(filters.updated_to)

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

    filters.next_due_from = make_naive(filters.next_due_from)
    filters.next_due_to = make_naive(filters.next_due_from)
    filters.created_from = make_naive(filters.created_from)
    filters.created_to = make_naive(filters.created_to)
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
    """
    List backup records matching filter criteria.

    Args:
        session (AsyncSession): Async database session.
        filters (BackupReportFilter): Filtering, ordering and pagination params.

    Returns:
        List[Backup]: Matching Backup ORM objects.
    """
    query = select(Backup)
    conditions = []

    # Filters
    if filters.backup_data:
        conditions.append(Backup.backup_data.in_(filters.backup_data))

    if filters.backup_status:
        conditions.append(Backup.backup_status.in_(filters.backup_status))

    filters.created_from = make_naive(filters.created_from)
    filters.created_to = make_naive(filters.created_to)

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

    filters.valid_from_from = make_naive(filters.valid_from_from)
    filters.valid_from_to = make_naive(filters.valid_from_to)
    filters.valid_to_from = make_naive(filters.valid_to_from)
    filters.valid_to_to = make_naive(filters.valid_to_to)
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


async def get_offers(
    session: AsyncSession,
    filters: OfferReportFilter
) -> List[Offer]:
    """
    Return list of Offer ORM objects. Joins OfferType when needed.
    Pagination is applied only when both limit>0 AND offset>0 are provided.
    But per your instruction, we will SKIP pagination if either limit==0 OR offset==0.
    """
    stmt = select(Offer).options(joinedload(Offer.offer_type))
    conditions = []

    # Basic filters
    if filters.offer_ids:
        conditions.append(Offer.offer_id.in_(filters.offer_ids))
    if filters.offer_names:
        conditions.append(Offer.offer_name.in_(filters.offer_names))
    if filters.is_special is not None:
        conditions.append(Offer.is_special.is_(filters.is_special))
    if filters.statuses:
        # Offer.status is an Enum column; the database stores the enum values.
        conditions.append(Offer.status.in_(filters.statuses))
    if filters.created_by:
        conditions.append(Offer.created_by.in_(filters.created_by))

    filters.created_from = make_naive(filters.created_from)
    filters.created_to = make_naive(filters.created_to)
    # created_at range
    if filters.created_from and filters.created_to:
        conditions.append(and_(Offer.created_at >= filters.created_from, Offer.created_at <= filters.created_to))
    elif filters.created_from:
        conditions.append(Offer.created_at >= filters.created_from)
    elif filters.created_to:
        conditions.append(Offer.created_at <= filters.created_to)

    # OfferType filters (by id or name) -> ensure join
    if filters.offer_type_ids or filters.offer_type_names:
        stmt = stmt.join(OfferType, Offer.offer_type)
        if filters.offer_type_ids:
            conditions.append(OfferType.offer_type_id.in_(filters.offer_type_ids))
        if filters.offer_type_names:
            conditions.append(OfferType.offer_type_name.in_(filters.offer_type_names))

    if conditions:
        stmt = stmt.where(and_(*conditions))

    # Ordering: support ordering by related offer_type_name
    order_col = None
    if filters.order_by in {"offer_id", "offer_name", "offer_validity", "is_special", "created_at", "status", "created_by"}:
        order_col = getattr(Offer, filters.order_by)
    elif filters.order_by == "offer_type_name":
        # join if not already
        stmt = stmt.join(OfferType, Offer.offer_type)
        order_col = OfferType.offer_type_name
    else:
        # fallback to created_at
        order_col = Offer.created_at

    stmt = stmt.order_by(asc(order_col) if filters.order_dir == "asc" else desc(order_col))

    # Pagination: Apply only when BOTH limit>0 AND offset>0, but per your instruction to skip pagination when either is zero:
    # Let's interpret "if limit or offset is zero then no need of pagination" -> we apply pagination only when (limit>0 and offset>0)
    if (filters.limit is not None and filters.offset is not None) and (filters.limit > 0 and filters.offset > 0):
        stmt = stmt.limit(filters.limit).offset(filters.offset)

    result = await session.execute(stmt)
    return result.scalars().unique().all()


async def get_plans(session: AsyncSession, filters: PlanReportFilter) -> List[Plan]:
    """
    Returns list of Plan ORM objects joined with PlanGroup (when needed).
    Pagination is applied only when both limit>0 AND offset>0; if either is 0 => skip pagination.
    """
    stmt = select(Plan).options(joinedload(Plan.group))
    conditions = []

    # ids / exact names
    if filters.plan_ids:
        conditions.append(Plan.plan_id.in_(filters.plan_ids))
    if filters.plan_names:
        conditions.append(Plan.plan_name.in_(filters.plan_names))

    # partial search on name (ILIKE for case-insensitive)
    if filters.name_search:
        # use func.lower for cross-db compatibility
        term = f"%{filters.name_search.strip().lower()}%"
        conditions.append(func.lower(Plan.plan_name).like(term))

    # price range
    if filters.min_price is not None and filters.max_price is not None:
        conditions.append(Plan.price.between(filters.min_price, filters.max_price))
    elif filters.min_price is not None:
        conditions.append(Plan.price >= filters.min_price)
    elif filters.max_price is not None:
        conditions.append(Plan.price <= filters.max_price)

    # validity range
    if filters.min_validity is not None and filters.max_validity is not None:
        conditions.append(Plan.validity.between(filters.min_validity, filters.max_validity))
    elif filters.min_validity is not None:
        conditions.append(Plan.validity >= filters.min_validity)
    elif filters.max_validity is not None:
        conditions.append(Plan.validity <= filters.max_validity)

    # enums & booleans
    if filters.plan_types:
        conditions.append(Plan.plan_type.in_(filters.plan_types))
    if filters.plan_statuses:
        conditions.append(Plan.status.in_(filters.plan_statuses))
    if filters.most_popular is not None:
        # SQLAlchemy boolean check
        if filters.most_popular:
            conditions.append(Plan.most_popular.is_(True))
        else:
            conditions.append(Plan.most_popular.is_(False))

    # group filters (join when needed)
    if filters.group_ids or filters.group_names:
        stmt = stmt.join(PlanGroup, Plan.group)
        if filters.group_ids:
            conditions.append(PlanGroup.group_id.in_(filters.group_ids))
        if filters.group_names:
            conditions.append(PlanGroup.group_name.in_(filters.group_names))

    # created_by
    if filters.created_by:
        conditions.append(Plan.created_by.in_(filters.created_by))

    filters.created_from = make_naive(filters.created_from)
    filters.created_to = make_naive(filters.created_to)
    # created_at range
    if filters.created_from and filters.created_to:
        conditions.append(and_(Plan.created_at >= filters.created_from, Plan.created_at <= filters.created_to))
    elif filters.created_from:
        conditions.append(Plan.created_at >= filters.created_from)
    elif filters.created_to:
        conditions.append(Plan.created_at <= filters.created_to)

    # apply where
    if conditions:
        stmt = stmt.where(and_(*conditions))

    # ordering: support group_name (join if needed)
    order_col = None
    if filters.order_by in {"plan_id", "plan_name", "price", "validity", "most_popular", "created_at", "plan_type", "status"}:
        order_col = getattr(Plan, filters.order_by)
    elif filters.order_by == "group_name":
        stmt = stmt.join(PlanGroup, Plan.group)
        order_col = PlanGroup.group_name
    else:
        order_col = Plan.created_at

    stmt = stmt.order_by(asc(order_col) if filters.order_dir == "asc" else desc(order_col))

    # Pagination: apply only when BOTH limit>0 AND offset>0; skip otherwise
    if (filters.limit is not None and filters.offset is not None) and (filters.limit > 0 and filters.offset > 0):
        stmt = stmt.limit(filters.limit).offset(filters.offset)

    result = await session.execute(stmt)
    return result.scalars().unique().all()


async def get_referrals(session: AsyncSession, filters: ReferralReportFilter) -> List[ReferralReward]:
    """
    Returns ReferralReward ORM objects joined with referrer and referred User objects.
    Pagination is applied only when limit>0 AND offset>0. If either is zero -> skip pagination.
    """
    stmt = select(ReferralReward).options(
        joinedload(ReferralReward.referrer),
        joinedload(ReferralReward.referred)
    )

    conditions = []

    if filters.reward_ids:
        conditions.append(ReferralReward.reward_id.in_(filters.reward_ids))
    if filters.referrer_ids:
        conditions.append(ReferralReward.referrer_id.in_(filters.referrer_ids))
    if filters.referred_ids:
        conditions.append(ReferralReward.referred_id.in_(filters.referred_ids))
    if filters.statuses:
        conditions.append(ReferralReward.status.in_(filters.statuses))

    # phone filters (need to join user tables only if provided)
    # joinedload already eager-loads, but if we want filtering by user phone we can join User explicitly
    if filters.referrer_phones:
        # join referrer user on referrer relationship via aliasing using select relationships isn't needed; use User table and filter by referrer_id
        # easiest: join User as referrer and filter on User.phone_number
        ref_user = User.__table__.alias("ref_user")
        stmt = stmt.join(ref_user, ref_user.c.user_id == ReferralReward.referrer_id)
        conditions.append(ref_user.c.phone_number.in_(filters.referrer_phones))

        # re-join for referred if both phone filters present, else we'll join again later
    if filters.referred_phones:
        referred_user = User.__table__.alias("referred_user")
        stmt = stmt.join(referred_user, referred_user.c.user_id == ReferralReward.referred_id)
        conditions.append(referred_user.c.phone_number.in_(filters.referred_phones))

    # reward amount range
    if (filters.min_amount is not None) and (filters.max_amount is not None):
        conditions.append(ReferralReward.reward_amount.between(filters.min_amount, filters.max_amount))
    elif filters.min_amount is not None:
        conditions.append(ReferralReward.reward_amount >= filters.min_amount)
    elif filters.max_amount is not None:
        conditions.append(ReferralReward.reward_amount <= filters.max_amount)


    filters.created_from = make_naive(filters.created_from)
    filters.created_to = make_naive(filters.created_to)
    filters.claimed_from = make_naive(filters.claimed_from)
    filters.claimed_to = make_naive(filters.claimed_to)
    # created_at range
    if filters.created_from and filters.created_to:
        conditions.append(and_(ReferralReward.created_at >= filters.created_from,
                               ReferralReward.created_at <= filters.created_to))
    elif filters.created_from:
        conditions.append(ReferralReward.created_at >= filters.created_from)
    elif filters.created_to:
        conditions.append(ReferralReward.created_at <= filters.created_to)

    # claimed_at range
    if filters.claimed_from and filters.claimed_to:
        conditions.append(and_(ReferralReward.claimed_at >= filters.claimed_from,
                               ReferralReward.claimed_at <= filters.claimed_to))
    elif filters.claimed_from:
        conditions.append(ReferralReward.claimed_at >= filters.claimed_from)
    elif filters.claimed_to:
        conditions.append(ReferralReward.claimed_at <= filters.claimed_to)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    # ordering (support referrer_name and referred_name by joining User table as needed)
    order_col = None
    if filters.order_by in {"reward_id", "reward_amount", "status", "created_at", "claimed_at"}:
        order_col = getattr(ReferralReward, filters.order_by)
    elif filters.order_by == "referrer_name":
        # join referrer user table if not already joined
        stmt = stmt.join(User, ReferralReward.referrer)  # safe to re-join
        order_col = User.name
    elif filters.order_by == "referred_name":
        stmt = stmt.join(User, ReferralReward.referred)
        order_col = User.name
    else:
        order_col = ReferralReward.created_at

    stmt = stmt.order_by(asc(order_col) if filters.order_dir == "asc" else desc(order_col))

    # Pagination: apply only when BOTH limit>0 AND offset>0, skip otherwise
    if (filters.limit is not None and filters.offset is not None) and (filters.limit > 0 and filters.offset > 0):
        stmt = stmt.limit(filters.limit).offset(filters.offset)

    result = await session.execute(stmt)
    return result.scalars().unique().all()


async def get_role_permissions(session: AsyncSession, filters: RolePermissionReportFilter) -> List[RolePermission]:
    """
    Return RolePermission ORM objects joined with Role and Permission.
    Pagination is applied only when both limit>0 and offset>0; otherwise skipped.
    """
    stmt = select(RolePermission).options(
        joinedload(RolePermission.role),
        joinedload(RolePermission.permission)
    )

    conditions = []

    if filters.role_permission_ids:
        conditions.append(RolePermission.id.in_(filters.role_permission_ids))
    if filters.role_ids:
        conditions.append(RolePermission.role_id.in_(filters.role_ids))
    if filters.permission_ids:
        conditions.append(RolePermission.permission_id.in_(filters.permission_ids))
    if filters.role_names:
        stmt = stmt.join(Role, RolePermission.role)
        conditions.append(Role.role_name.in_(filters.role_names))
    if filters.resources:
        stmt = stmt.join(Permission, RolePermission.permission)
        conditions.append(Permission.resource.in_(filters.resources))

    # boolean filters
    if filters.read is not None:
        stmt = stmt.join(Permission, RolePermission.permission)
        conditions.append(Permission.read.is_(filters.read))
    if filters.write is not None:
        stmt = stmt.join(Permission, RolePermission.permission)
        conditions.append(Permission.write.is_(filters.write))
    if filters.edit is not None:
        stmt = stmt.join(Permission, RolePermission.permission)
        conditions.append(Permission.edit.is_(filters.edit))
    if filters.delete is not None:
        stmt = stmt.join(Permission, RolePermission.permission)
        conditions.append(Permission.delete.is_(filters.delete))

    if conditions:
        stmt = stmt.where(and_(*conditions))

    # ordering
    order_col = None
    if filters.order_by in {"id", "role_id", "permission_id"}:
        order_col = getattr(RolePermission, filters.order_by)
    elif filters.order_by == "role_name":
        stmt = stmt.join(Role, RolePermission.role)
        order_col = Role.role_name
    elif filters.order_by == "resource":
        stmt = stmt.join(Permission, RolePermission.permission)
        order_col = Permission.resource
    elif filters.order_by in {"read", "write", "edit", "delete"}:
        stmt = stmt.join(Permission, RolePermission.permission)
        order_col = getattr(Permission, filters.order_by)
    else:
        order_col = RolePermission.id

    stmt = stmt.order_by(asc(order_col) if filters.order_dir == "asc" else desc(order_col))

    # pagination
    if (filters.limit is not None and filters.offset is not None) and (filters.limit > 0 and filters.offset > 0):
        stmt = stmt.limit(filters.limit).offset(filters.offset)

    result = await session.execute(stmt)
    return result.scalars().unique().all()


async def get_sessions(session: AsyncSession, filters: SessionsReportFilter) -> List[Session]:
    """
    Build query with many filter options. Pagination is applied only when BOTH
    limit>0 AND offset>0. Per your rule: if limit OR offset is zero => skip pagination.
    """
    stmt = select(Session)
    conditions = []

    # Normalize datetimes to naive UTC to avoid asyncpg timezone errors
    filters.refresh_expires_from = make_naive(filters.refresh_expires_from)
    filters.refresh_expires_to = make_naive(filters.refresh_expires_to)
    filters.login_time_from = make_naive(filters.login_time_from)
    filters.login_time_to = make_naive(filters.login_time_to)
    filters.last_active_from = make_naive(filters.last_active_from)
    filters.last_active_to = make_naive(filters.last_active_to)
    filters.revoked_from = make_naive(filters.revoked_from)
    filters.revoked_to = make_naive(filters.revoked_to)

    # IDs and basic filters
    if filters.session_ids:
        conditions.append(Session.session_id.in_(filters.session_ids))
    if filters.user_ids:
        conditions.append(Session.user_id.in_(filters.user_ids))
    if filters.is_active is not None:
        conditions.append(Session.is_active.is_(filters.is_active))

    if filters.jtis:
        conditions.append(Session.jti.in_(filters.jtis))
    if filters.refresh_tokens_contains:
        # case-insensitive substring search
        term = f"%{filters.refresh_tokens_contains}%"
        conditions.append(Session.refresh_token.ilike(term))

    # datetime ranges
    if filters.refresh_expires_from and filters.refresh_expires_to:
        conditions.append(and_(Session.refresh_token_expires_at >= filters.refresh_expires_from,
                               Session.refresh_token_expires_at <= filters.refresh_expires_to))
    elif filters.refresh_expires_from:
        conditions.append(Session.refresh_token_expires_at >= filters.refresh_expires_from)
    elif filters.refresh_expires_to:
        conditions.append(Session.refresh_token_expires_at <= filters.refresh_expires_to)

    if filters.login_time_from and filters.login_time_to:
        conditions.append(and_(Session.login_time >= filters.login_time_from,
                               Session.login_time <= filters.login_time_to))
    elif filters.login_time_from:
        conditions.append(Session.login_time >= filters.login_time_from)
    elif filters.login_time_to:
        conditions.append(Session.login_time <= filters.login_time_to)

    if filters.last_active_from and filters.last_active_to:
        conditions.append(and_(Session.last_active >= filters.last_active_from,
                               Session.last_active <= filters.last_active_to))
    elif filters.last_active_from:
        conditions.append(Session.last_active >= filters.last_active_from)
    elif filters.last_active_to:
        conditions.append(Session.last_active <= filters.last_active_to)

    if filters.revoked_from and filters.revoked_to:
        conditions.append(and_(Session.revoked_at >= filters.revoked_from,
                               Session.revoked_at <= filters.revoked_to))
    elif filters.revoked_from:
        conditions.append(Session.revoked_at >= filters.revoked_from)
    elif filters.revoked_to:
        conditions.append(Session.revoked_at <= filters.revoked_to)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    # Ordering
    order_col = getattr(Session, filters.order_by)
    stmt = stmt.order_by(asc(order_col) if filters.order_dir == "asc" else desc(order_col))

    # Pagination: apply only when BOTH limit>0 AND offset>0
    if (filters.limit is not None and filters.offset is not None) and (filters.limit > 0 and filters.offset > 0):
        stmt = stmt.limit(filters.limit).offset(filters.offset)

    result = await session.execute(stmt)
    return result.scalars().unique().all()


async def get_transactions(session: AsyncSession, filters: TransactionsReportFilter) -> List[Transaction]:
    """
    Build and execute a query over Transactions with many filter combinations.
    Pagination is applied only when both limit>0 and offset>0 (skip otherwise).
    """
    stmt = select(Transaction)
    conditions = []

    # Normalize datetime filters to naive UTC
    filters.created_from = make_naive(filters.created_from)
    filters.created_to = make_naive(filters.created_to)

    # Basic id filters
    if filters.txn_ids:
        conditions.append(Transaction.txn_id.in_(filters.txn_ids))
    if filters.user_ids:
        conditions.append(Transaction.user_id.in_(filters.user_ids))

    # Enums and types
    if filters.categories:
        conditions.append(Transaction.category.in_(filters.categories))
    if filters.txn_types:
        conditions.append(Transaction.txn_type.in_(filters.txn_types))

    # amount range
    if filters.min_amount is not None and filters.max_amount is not None:
        conditions.append(Transaction.amount.between(filters.min_amount, filters.max_amount))
    elif filters.min_amount is not None:
        conditions.append(Transaction.amount >= filters.min_amount)
    elif filters.max_amount is not None:
        conditions.append(Transaction.amount <= filters.max_amount)

    # service / plan / offer
    if filters.service_types:
        conditions.append(Transaction.service_type.in_(filters.service_types))
    if filters.plan_ids:
        conditions.append(Transaction.plan_id.in_(filters.plan_ids))
    if filters.offer_ids:
        conditions.append(Transaction.offer_id.in_(filters.offer_ids))

    # phone filters
    if filters.from_phone_numbers:
        conditions.append(Transaction.from_phone_number.in_(filters.from_phone_numbers))
    if filters.to_phone_numbers:
        conditions.append(Transaction.to_phone_number.in_(filters.to_phone_numbers))

    # source/status/payment method
    if filters.sources:
        conditions.append(Transaction.source.in_(filters.sources))
    if filters.statuses:
        conditions.append(Transaction.status.in_(filters.statuses))
    if filters.payment_methods:
        conditions.append(Transaction.payment_method.in_(filters.payment_methods))
    if filters.payment_transaction_id_contains:
        term = f"%{filters.payment_transaction_id_contains}%"
        conditions.append(Transaction.payment_transaction_id.ilike(term))

    # created_at
    if filters.created_from and filters.created_to:
        conditions.append(and_(Transaction.created_at >= filters.created_from, Transaction.created_at <= filters.created_to))
    elif filters.created_from:
        conditions.append(Transaction.created_at >= filters.created_from)
    elif filters.created_to:
        conditions.append(Transaction.created_at <= filters.created_to)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    # ordering
    order_col = getattr(Transaction, filters.order_by)
    stmt = stmt.order_by(asc(order_col) if filters.order_dir == "asc" else desc(order_col))

    # Pagination: apply only when both limit>0 AND offset>0 (per instruction to skip if either is zero)
    if (filters.limit is not None and filters.offset is not None) and (filters.limit > 0 and filters.offset > 0):
        stmt = stmt.limit(filters.limit).offset(filters.offset)

    result = await session.execute(stmt)
    return result.scalars().unique().all()


async def get_users_archive(session: AsyncSession, filters: UsersArchiveFilter) -> List[UserArchieve]:
    """
    Returns list of UserArchieve ORM objects matching filters.
    Pagination applied only when both limit>0 and offset>0.
    """
    stmt = select(UserArchieve)
    conditions = []

    # normalize datetimes
    filters.created_from = make_naive(filters.created_from)
    filters.created_to   = make_naive(filters.created_to)
    filters.deleted_from = make_naive(filters.deleted_from)
    filters.deleted_to   = make_naive(filters.deleted_to)

    # basic id filters
    if filters.user_ids:
        conditions.append(UserArchieve.user_id.in_(filters.user_ids))

    # text search: name_search uses case-insensitive contains
    if filters.name_search:
        term = f"%{filters.name_search.strip().lower()}%"
        conditions.append(func.lower(UserArchieve.name).like(term))

    if filters.emails:
        conditions.append(UserArchieve.email.in_(filters.emails))
    if filters.phone_numbers:
        conditions.append(UserArchieve.phone_number.in_(filters.phone_numbers))

    # enums
    if filters.user_types:
        conditions.append(UserArchieve.user_type.in_(filters.user_types))
    if filters.statuses:
        conditions.append(UserArchieve.status.in_(filters.statuses))

    # wallet range (Numeric column)
    if filters.min_wallet is not None and filters.max_wallet is not None:
        conditions.append(UserArchieve.wallet_balance.between(filters.min_wallet, filters.max_wallet))
    elif filters.min_wallet is not None:
        conditions.append(UserArchieve.wallet_balance >= filters.min_wallet)
    elif filters.max_wallet is not None:
        conditions.append(UserArchieve.wallet_balance <= filters.max_wallet)

    # created_at range
    if filters.created_from and filters.created_to:
        conditions.append(and_(UserArchieve.created_at >= filters.created_from,
                               UserArchieve.created_at <= filters.created_to))
    elif filters.created_from:
        conditions.append(UserArchieve.created_at >= filters.created_from)
    elif filters.created_to:
        conditions.append(UserArchieve.created_at <= filters.created_to)

    # deleted_at range
    if filters.deleted_from and filters.deleted_to:
        conditions.append(and_(UserArchieve.deleted_at >= filters.deleted_from,
                               UserArchieve.deleted_at <= filters.deleted_to))
    elif filters.deleted_from:
        conditions.append(UserArchieve.deleted_at >= filters.deleted_from)
    elif filters.deleted_to:
        conditions.append(UserArchieve.deleted_at <= filters.deleted_to)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    # ordering
    # defensive getattr in case of typo
    try:
        order_col = getattr(UserArchieve, filters.order_by)
    except Exception:
        order_col = UserArchieve.deleted_at

    stmt = stmt.order_by(asc(order_col) if filters.order_dir == "asc" else desc(order_col))

    # pagination: apply only when BOTH >0
    if (filters.limit is not None and filters.offset is not None) and (filters.limit > 0 and filters.offset > 0):
        stmt = stmt.limit(filters.limit).offset(filters.offset)

    result = await session.execute(stmt)
    return result.scalars().unique().all()


async def get_users(
    session: AsyncSession,
    filters: UsersReportFilter
) -> List[User]:
    """
    List users matching report filters; supports many filters and optional pagination.

    Args:
        session (AsyncSession): Async database session.
        filters (UsersReportFilter): Filtering, ordering and pagination parameters.

    Returns:
        List[User]: Matching User ORM objects.
    """
    stmt = select(User)
    conditions = []

    # normalize datetimes
    filters.created_from = make_naive(filters.created_from)
    filters.created_to = make_naive(filters.created_to)
    filters.updated_from = make_naive(filters.updated_from)
    filters.updated_to = make_naive(filters.updated_to)

    # basic filters
    if filters.user_ids:
        conditions.append(User.user_id.in_(filters.user_ids))
    if filters.emails:
        conditions.append(User.email.in_(filters.emails))
    if filters.phone_numbers:
        conditions.append(User.phone_number.in_(filters.phone_numbers))

    # name_search (case-insensitive partial)
    if filters.name_search:
        term = f"%{filters.name_search.strip().lower()}%"
        conditions.append(func.lower(User.name).like(term))

    # enums
    if filters.user_types:
        conditions.append(User.user_type.in_(filters.user_types))
    if filters.statuses:
        conditions.append(User.status.in_(filters.statuses))

    # wallet range
    if filters.min_wallet is not None and filters.max_wallet is not None:
        conditions.append(User.wallet_balance.between(filters.min_wallet, filters.max_wallet))
    elif filters.min_wallet is not None:
        conditions.append(User.wallet_balance >= filters.min_wallet)
    elif filters.max_wallet is not None:
        conditions.append(User.wallet_balance <= filters.max_wallet)

    # created / updated ranges
    if filters.created_from and filters.created_to:
        conditions.append(and_(User.created_at >= filters.created_from, User.created_at <= filters.created_to))
    elif filters.created_from:
        conditions.append(User.created_at >= filters.created_from)
    elif filters.created_to:
        conditions.append(User.created_at <= filters.created_to)

    if filters.updated_from and filters.updated_to:
        conditions.append(and_(User.updated_at >= filters.updated_from, User.updated_at <= filters.updated_to))
    elif filters.updated_from:
        conditions.append(User.updated_at >= filters.updated_from)
    elif filters.updated_to:
        conditions.append(User.updated_at <= filters.updated_to)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    # ordering
    # guard against invalid order_by with getattr fallback
    if hasattr(User, filters.order_by):
        order_col = getattr(User, filters.order_by)
    else:
        order_col = User.created_at

    stmt = stmt.order_by(asc(order_col) if filters.order_dir == "asc" else desc(order_col))

    # Pagination: only when BOTH limit>0 AND offset>0 (skip otherwise)
    if (filters.limit is not None and filters.offset is not None) and (filters.limit > 0 and filters.offset > 0):
        stmt = stmt.limit(filters.limit).offset(filters.offset)

    result = await session.execute(stmt)
    return result.scalars().unique().all()