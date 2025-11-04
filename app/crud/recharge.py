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
    result = await db.execute(select(User).where(User.phone_number == phone))
    user = result.scalars().first()
    if not user:
        raise ValueError(f"User with phone {phone} not found")
    return user


async def count_active_plans(db: AsyncSession, user_id: int, phone: str) -> int:
    result = await db.execute(
        select(func.count()).where(
            CurrentActivePlan.user_id == user_id,
            CurrentActivePlan.phone_number == phone,
            CurrentActivePlan.status == CurrentPlanStatus.active,
        )
    )
    return result.scalar_one()


async def activate_queued_plan(db: AsyncSession, user_id: int, phone_number: str) -> None:
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
    for p in expired.scalars().all():
        p.status = CurrentPlanStatus.expired
        db.add(p)

    # Activate earliest queued plan
    queued = await db.execute(
        select(CurrentActivePlan)
        .where(
            CurrentActivePlan.user_id == user_id,
            CurrentActivePlan.phone_number == phone_number,
            CurrentActivePlan.status == CurrentPlanStatus.queued,
        )
        .order_by(CurrentActivePlan.valid_from)
    )
    plan = queued.scalars().first()
    if plan and plan.valid_from <= now:
        plan.status = CurrentPlanStatus.active
        db.add(plan)

    await db.commit()


# ---------- Plan ----------
async def get_plan_by_id(db: AsyncSession, plan_id: int) -> Plan:
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

    stmt = (
        select(CurrentActivePlan)
        .options(
            selectinload(CurrentActivePlan.plan),
            selectinload(CurrentActivePlan.user),
        )
    )

    # ------------------- FILTERS -------------------
    if f.phone_number:
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
    stmt = stmt.offset((f.page - 1) * f.size).limit(f.size)

    result = await db.execute(stmt)
    plans = result.scalars().all()

    return plans, total


# ---------- Transaction ----------
async def create_transaction(
    db: AsyncSession,
    **kwargs,
) -> Transaction:
    txn = Transaction(**kwargs)
    db.add(txn)
    await db.flush()
    return txn


async def list_transactions(
    db: AsyncSession,
    f: TransactionFilterParams,
) -> Tuple[List[Transaction], int]:

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