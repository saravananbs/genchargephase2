from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import desc, asc, and_, or_, func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas.recharge import CurrentPlanFilterParams, SortOrder, TransactionFilterParams, SortBy
from ..models.users import User
from ..models.plans import Plan, PlanStatus
from ..models.offers import Offer, OfferStatus
from ..models.transactions import Transaction, TransactionStatus, TransactionSource
from ..models.current_active_plans import CurrentActivePlan, CurrentPlanStatus


# ---------- Helpers ----------
async def get_user_by_phone(db: AsyncSession, phone: str) -> User:
    """
    Fetch a User by phone number.

    Args:
        db (AsyncSession): Async database session.
        phone (str): Phone number to search for.

    Returns:
        User: The matching User instance.

    Raises:
        ValueError: If no user with the given phone number exists.
    """
    result = await db.execute(select(User).where(User.phone_number == phone))
    user = result.scalars().first()
    if not user:
        raise ValueError(f"User with phone {phone} not found")
    return user


async def count_active_plans(db: AsyncSession, user_id: int, phone: str) -> int:
    """
    Count the number of active plans for a given user and phone number.

    Args:
        db (AsyncSession): Async database session.
        user_id (int): ID of the user.
        phone (str): Phone number associated with the plans.

    Returns:
        int: Number of active plans.
    """
    result = await db.execute(
        select(func.count()).where(
            CurrentActivePlan.user_id == user_id,
            CurrentActivePlan.phone_number == phone,
            CurrentActivePlan.status == CurrentPlanStatus.active,
        )
    )
    return result.scalar_one()


async def activate_queued_plan(db: AsyncSession, user_id: int, phone_number: str) -> None:
    """
    Expire outdated active plans and activate the earliest queued plan for a user/phone.

    This will update plan statuses and commit the transaction.

    Args:
        db (AsyncSession): Async database session.
        user_id (int): ID of the user.
        phone_number (str): Phone number associated with the plans.

    Returns:
        None
    """
    now = datetime.utcnow()

    # Expire old active plans
    expired = await db.execute(
        select(CurrentActivePlan).where(
            CurrentActivePlan.user_id == user_id,
            CurrentActivePlan.phone_number == phone_number,
            CurrentActivePlan.status == CurrentPlanStatus.active,
            CurrentActivePlan.valid_to < now,
        )
    )
    for plan in expired.scalars().all():
        plan.status = CurrentPlanStatus.expired
        db.add(plan)

    active_stmt = select(CurrentActivePlan).where(
        CurrentActivePlan.user_id == user_id,
        CurrentActivePlan.phone_number == phone_number,
        CurrentActivePlan.status == CurrentPlanStatus.active,
    ).order_by(CurrentActivePlan.valid_from)
    active_plan = await db.execute(active_stmt)
    has_active = active_plan.scalars().first()
    if not has_active:
        queued_stmt = (
            select(CurrentActivePlan)
            .where(
                CurrentActivePlan.user_id == user_id,
                CurrentActivePlan.phone_number == phone_number,
                CurrentActivePlan.status == CurrentPlanStatus.queued,
            )
            .order_by(CurrentActivePlan.valid_from)
        )
        queued_plan_result = await db.execute(queued_stmt)
        next_plan = queued_plan_result.scalars().first()
        if next_plan:
            if next_plan.valid_from > now:
                next_plan.valid_from = now
            next_plan.status = CurrentPlanStatus.active
            db.add(next_plan)

    await db.commit()


# ---------- Plan ----------
async def get_plan_by_id(db: AsyncSession, plan_id: int) -> Plan:
    """
    Retrieve an active Plan by ID, raising on not found or inactive.

    Args:
        db (AsyncSession): Async database session.
        plan_id (int): Primary key of the plan.

    Returns:
        Plan: The active Plan instance.

    Raises:
        ValueError: If plan not found or inactive.
    """
    result = await db.execute(
        select(Plan)
        .options(selectinload(Plan.group))
        .where(Plan.plan_id == plan_id, Plan.status == PlanStatus.active)
    )
    plan = result.scalars().first()
    if not plan:
        raise ValueError("Plan not found or inactive")
    return plan


# ---------- Offer ----------
async def get_offer_by_id(db: AsyncSession, offer_id: int) -> Offer:
    """
    Retrieve an active Offer by ID, raising if not found or inactive.

    Args:
        db (AsyncSession): Async database session.
        offer_id (int): Primary key of the offer.

    Returns:
        Offer: The Offer instance.

    Raises:
        ValueError: If offer not found or inactive.
    """
    result = await db.execute(
        select(Offer)
        .options(selectinload(Offer.offer_type))
        .where(Offer.offer_id == offer_id, Offer.status == OfferStatus.active)
    )
    offer = result.scalars().first()
    if not offer:
        raise ValueError("Offer not found or inactive")
    return offer


# ---------- CurrentActivePlan ----------
async def create_active_plan(
    db: AsyncSession,
    user_id: int,
    plan_id: int,
    phone_number: str,
    valid_from: datetime,
    valid_to: datetime,
    status: CurrentPlanStatus,
) -> CurrentActivePlan:
    """
    Create a CurrentActivePlan instance (not yet committed).

    Args:
        db (AsyncSession): Async database session.
        user_id (int): User who owns the plan.
        plan_id (int): Plan identifier.
        phone_number (str): Phone number associated with the plan.
        valid_from (datetime): Plan start datetime.
        valid_to (datetime): Plan end datetime.
        status (CurrentPlanStatus): Initial plan status.

    Returns:
        CurrentActivePlan: The new in-session CurrentActivePlan instance.
    """
    plan = CurrentActivePlan(
        user_id=user_id,
        plan_id=plan_id,
        phone_number=phone_number,
        valid_from=valid_from,
        valid_to=valid_to,
        status=status,
    )
    db.add(plan)
    await db.flush()
    return plan


async def list_active_plans(
    db: AsyncSession,
    f: CurrentPlanFilterParams,
) -> Tuple[List[CurrentActivePlan], int]:

    """
    List active/current plans with flexible filtering, sorting and pagination.

    Args:
        db (AsyncSession): Async database session.
        f (CurrentPlanFilterParams): Filtering, sorting and pagination parameters.

    Returns:
        Tuple[List[CurrentActivePlan], int]: (list of plans, total count).
    """
    stmt = (
        select(CurrentActivePlan)
        .options(
            selectinload(CurrentActivePlan.plan),
            selectinload(CurrentActivePlan.user),
        )
    )
    # ------------------- FILTERS -------------------
    if f.phone_number:
        user_id = await get_user_by_phone(db=db, phone=f.phone_number)
        await activate_queued_plan(db=db, phone_number=f.phone_number, user_id=user_id.user_id)
        stmt = stmt.where(CurrentActivePlan.phone_number == f.phone_number)

    if f.phone_number_like:
        like_pattern = f"%{f.phone_number_like}%"
        stmt = stmt.where(CurrentActivePlan.phone_number.ilike(like_pattern))

    if f.plan_id:
        stmt = stmt.where(CurrentActivePlan.plan_id == f.plan_id)

    if f.status:
        stmt = stmt.where(CurrentActivePlan.status == f.status)

    # valid_from range
    if f.valid_from_start:
        stmt = stmt.where(CurrentActivePlan.valid_from >= f.valid_from_start)
    if f.valid_from_end:
        stmt = stmt.where(CurrentActivePlan.valid_from <= f.valid_from_end)

    # valid_to range
    if f.valid_to_start:
        stmt = stmt.where(CurrentActivePlan.valid_to >= f.valid_to_start)
    if f.valid_to_end:
        stmt = stmt.where(CurrentActivePlan.valid_to <= f.valid_to_end)

    # validity length (days)
    if f.validity_days_min is not None or f.validity_days_max is not None:
        # (valid_to - valid_from)  ->  days
        delta = func.date_part('day', CurrentActivePlan.valid_to - CurrentActivePlan.valid_from)
        if f.validity_days_min is not None:
            stmt = stmt.where(delta >= f.validity_days_min)
        if f.validity_days_max is not None:
            stmt = stmt.where(delta <= f.validity_days_max)

    # ------------------- TOTAL COUNT -------------------
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    # ------------------- SORTING -------------------
    order_col = {
        "valid_from": CurrentActivePlan.valid_from,
        "valid_to":   CurrentActivePlan.valid_to,
    }.get(f.sort_by or "valid_to", CurrentActivePlan.valid_to)

    order_fn = desc if f.sort_order == SortOrder.desc else asc
    stmt = stmt.order_by(order_fn(order_col))

    # ------------------- PAGINATION -------------------
    if f.page > 0 or f.size > 0:
        stmt = stmt.offset((f.page - 1) * f.size).limit(f.size)

    result = await db.execute(stmt)
    plans = result.scalars().all()

    return plans, total


# ---------- Transaction ----------
async def create_transaction(
    db: AsyncSession,
    **kwargs,
) -> Transaction:
    """
    Create a Transaction ORM instance and add it to the current session.

    Args:
        db (AsyncSession): Async database session.
        **kwargs: Fields for the Transaction model.

    Returns:
        Transaction: The newly created Transaction instance (not committed).
    """
    txn = Transaction(**kwargs)
    db.add(txn)
    await db.flush()
    return txn


async def list_transactions(
    db: AsyncSession,
    f: TransactionFilterParams,
) -> Tuple[List[Transaction], int]:

    """
    List transactions applying provided filters, sorting and pagination.

    Args:
        db (AsyncSession): Async database session.
        f (TransactionFilterParams): Filtering, sorting and pagination params.

    Returns:
        Tuple[List[Transaction], int]: (list of transactions, total count).
    """
    stmt = select(Transaction)

    # ------------------- FILTERS -------------------
    if f.user_id:
        stmt = stmt.where(Transaction.user_id == f.user_id)

    if f.category:
        stmt = stmt.where(Transaction.category == f.category)

    if f.txn_type:
        stmt = stmt.where(Transaction.txn_type == f.txn_type)

    if f.service_type:
        stmt = stmt.where(Transaction.service_type == f.service_type)

    if f.source:
        stmt = stmt.where(Transaction.source == f.source)

    if f.status:
        stmt = stmt.where(Transaction.status == f.status)

    if f.payment_method:
        stmt = stmt.where(Transaction.payment_method == f.payment_method)

    # phone numbers – exact + LIKE
    if f.from_phone_number:
        stmt = stmt.where(Transaction.from_phone_number == f.from_phone_number)
    if f.from_phone_number_like:
        stmt = stmt.where(
            Transaction.from_phone_number.ilike(f"%{f.from_phone_number_like}%")
        )

    if f.to_phone_number:
        stmt = stmt.where(Transaction.to_phone_number == f.to_phone_number)
    if f.to_phone_number_like:
        stmt = stmt.where(
            Transaction.to_phone_number.ilike(f"%{f.to_phone_number_like}%")
        )

    # amount range
    if f.amount_min is not None:
        stmt = stmt.where(Transaction.amount >= f.amount_min)
    if f.amount_max is not None:
        stmt = stmt.where(Transaction.amount <= f.amount_max)

    # created_at range (date only – compare with midnight)
    if f.created_at_start:
        stmt = stmt.where(Transaction.created_at >= f.created_at_start)
    if f.created_at_end:
        # end of day inclusive
        stmt = stmt.where(
            Transaction.created_at < (f.created_at_end + datetime.timedelta(days=1))
        )

    # ------------------- TOTAL COUNT -------------------
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    # ------------------- SORTING -------------------
    order_map = {
        SortBy.created_at: Transaction.created_at,
        SortBy.amount: Transaction.amount,
    }
    col = order_map[f.sort_by]
    order_fn = desc if f.sort_order == SortOrder.desc else asc
    stmt = stmt.order_by(order_fn(col))

    # ------------------- PAGINATION -------------------
    if f.size == 0:          # return everything
        result = await db.execute(stmt)
    else:
        stmt = stmt.offset((f.page - 1) * f.size).limit(f.size)
        result = await db.execute(stmt)

    txns = result.scalars().all()
    return txns, total