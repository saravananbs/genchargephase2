# app/services/autopay.py
from datetime import datetime, timedelta
from typing import Sequence
from math import ceil

from sqlalchemy.ext.asyncio import AsyncSession

from ..crud.autopay import (
    create_autopay,
    get_autopay,
    get_multi_by_user,
    get_multi_all,
    update_autopay,
    delete_autopay,
    get_due_autopays,
)
from ..schemas.autopay import (
    AutoPayCreate,
    AutoPayUpdate,
    AutoPayOut,
    PaginatedAutoPay,
    PaginatedAutoPayAdmin,
    AutoPayOutAdmin,
    AutoPayStatus,
    AutoPayTag,
)
from ..schemas.users import UserResponse
from ..schemas.plans import PlanResponse
from fastapi import HTTPException
from starlette import status
from ..services.recharge import subscribe_plan, RechargeRequest, TransactionSource, PaymentMethod


async def create_user_autopay(
    db: AsyncSession, *, obj_in: AutoPayCreate, current_user_id: int
) -> AutoPayOut:
    """
    Create an autopay configuration for the current user.

    Args:
        db (AsyncSession): Async database session.
        obj_in (AutoPayCreate): Autopay configuration data.
        current_user_id (int): ID of the user creating the autopay.

    Returns:
        AutoPayOut: Validated autopay DTO.

    Raises:
        Any exceptions from the underlying CRUD layer are propagated.
    """
    autopay = await create_autopay(db, obj_in=obj_in, user_id=current_user_id)
    return AutoPayOut.model_validate(autopay)


async def get_user_autopay(
    db: AsyncSession, *, autopay_id: int, current_user_id: int
) -> AutoPayOut:
    """
    Retrieve a single autopay configuration for the current user.

    Args:
        db (AsyncSession): Async database session.
        autopay_id (int): ID of the autopay to retrieve.
        current_user_id (int): ID of the current user (for authorization).

    Returns:
        AutoPayOut: Validated autopay DTO.

    Raises:
        HTTPException: 404 if the autopay is not found or the user is not authorized.
    """
    autopay = await get_autopay(db, autopay_id=autopay_id, user_id=current_user_id)
    if not autopay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AutoPay not found",
            headers={"X-Error": "Item not found in database"},
        )
    return AutoPayOut.model_validate(autopay)


async def list_user_autopays(
    db: AsyncSession,
    *,
    current_user_id: int,
    page: int = 0,
    size: int = 0,
    status: AutoPayStatus | None = None,
    tag: AutoPayTag | None = None,
    sort: str = "created_at_desc",
    phone_number: str | None = None
) -> PaginatedAutoPay:
    """
    List autopay configurations for the current user with pagination and filtering.

    Args:
        db (AsyncSession): Async database session.
        current_user_id (int): ID of the current user.
        page (int): Page number for pagination (default: 1).
        size (int): Page size (default: 20).
        status (AutoPayStatus | None): Optional status filter.
        tag (AutoPayTag | None): Optional tag filter (e.g., regular, one-time).
        sort (str): Sort key (default: "created_at_desc").
        phone_number (str | None): Optional phone number filter.

    Returns:
        PaginatedAutoPay: Paginated list of autopay DTOs with metadata.
    """
    rows, total = await get_multi_by_user(
        db,
        user_id=current_user_id,
        phone_number=phone_number,
        page=page,
        size=size,
        status=status,
        tag=tag,
        sort=sort,
    )
    return PaginatedAutoPay(
        items=[AutoPayOut.model_validate(r) for r in rows],
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if size else 0,
    )


async def update_user_autopay(
    db: AsyncSession, *, autopay_id: int, obj_in: AutoPayUpdate, current_user_id: int
) -> AutoPayOut:
    """
    Update an autopay configuration for the current user.

    Args:
        db (AsyncSession): Async database session.
        autopay_id (int): ID of the autopay to update.
        obj_in (AutoPayUpdate): Updated autopay data.
        current_user_id (int): ID of the current user (for authorization).

    Returns:
        AutoPayOut: Updated autopay DTO.

    Raises:
        HTTPException: 404 if the autopay is not found or the user is not authorized.
    """
    autopay = await get_autopay(db, autopay_id=autopay_id, user_id=current_user_id)
    if not autopay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AutoPay not found",
            headers={"X-Error": "Item not found in database"},
        )
    updated = await update_autopay(db, db_obj=autopay, obj_in=obj_in)
    return AutoPayOut.model_validate(updated)


async def delete_user_autopay(
    db: AsyncSession, *, autopay_id: int, current_user_id: int
) -> None:
    """
    Delete an autopay configuration for the current user.

    Args:
        db (AsyncSession): Async database session.
        autopay_id (int): ID of the autopay to delete.
        current_user_id (int): ID of the current user (for authorization).

    Returns:
        None.

    Raises:
        HTTPException: 404 if the autopay is not found or the user is not authorized.
    """
    autopay = await get_autopay(db, autopay_id=autopay_id, user_id=current_user_id)
    if not autopay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AutoPay not found",
            headers={"X-Error": "Item not found in database"},
        )
    await delete_autopay(db, db_obj=autopay)


# ---------- Admin ----------
async def list_all_autopays(
    db: AsyncSession,
    *,
    page: int = 0,
    size: int = 0,
    phone_number: str | None = None,
    status: AutoPayStatus | None = None,
    tag: AutoPayTag | None = None,
    sort: str = "created_at_desc",
) -> PaginatedAutoPayAdmin:
    """
    List all autopay configurations (admin view) with pagination and filtering.

    Args:
        db (AsyncSession): Async database session.
        page (int): Page number (default: 1).
        size (int): Page size (default: 20).
        phone_number (str | None): Optional phone number filter.
        status (AutoPayStatus | None): Optional status filter.
        tag (AutoPayTag | None): Optional tag filter.
        sort (str): Sort key (default: "created_at_desc").

    Returns:
        PaginatedAutoPay: Paginated list of all autopays with metadata.
    """
    rows, total = await get_multi_all(
        db, page=page, size=size, status=status, tag=tag, sort=sort, phone_number=phone_number
    )
    # Build nested details in bulk to avoid N+1 queries
    if not rows:
        return PaginatedAutoPayAdmin(items=[], total=0, page=page, size=size, pages=0)

    # Collect keys
    user_ids = {r.user_id for r in rows}
    plan_ids = {r.plan_id for r in rows}
    phone_numbers = {r.phone_number for r in rows}

    # Fetch related models in bulk
    from sqlalchemy import select
    from ..models.users import User
    from ..models.plans import Plan

    users_by_id: dict[int, User] = {}
    phone_users_by_number: dict[str, User] = {}
    plans_by_id: dict[int, Plan] = {}

    if user_ids:
        res = await db.execute(select(User).where(User.user_id.in_(user_ids)))
        users = res.scalars().all()
        users_by_id = {u.user_id: u for u in users}
    if phone_numbers:
        res = await db.execute(select(User).where(User.phone_number.in_(phone_numbers)))
        phone_users = res.scalars().all()
        phone_users_by_number = {u.phone_number: u for u in phone_users}
    if plan_ids:
        res = await db.execute(select(Plan).where(Plan.plan_id.in_(plan_ids)))
        plans = res.scalars().all()
        plans_by_id = {p.plan_id: p for p in plans}

    items: list[AutoPayOutAdmin] = []
    for ap in rows:
        id_user = users_by_id.get(ap.user_id)
        phone_user = phone_users_by_number.get(ap.phone_number)
        plan = plans_by_id.get(ap.plan_id)

        item = AutoPayOutAdmin(
            autopay_id=ap.autopay_id,
            user_id=ap.user_id,
            plan_id=ap.plan_id,
            status=ap.status,
            phone_number=ap.phone_number,
            tag=ap.tag,
            next_due_date=ap.next_due_date,
            created_at=ap.created_at,
            id_user_details=(None if id_user is None else UserResponse.model_validate(id_user)),
            phone_user_details=(None if phone_user is None else UserResponse.model_validate(phone_user)),
            plan_details=(None if plan is None else PlanResponse.model_validate(plan)),
        )
        items.append(item)

    return PaginatedAutoPayAdmin(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if size else 0,
    )


async def process_due_autopays(db: AsyncSession, now: datetime | None = None) -> list[dict]:
    """
    Process autopays that are due and attempt to subscribe plans, update next due dates.

    Retrieves all autopays with due dates <= now, attempts subscription via recharge service,
    and updates regular autopays' next_due_date based on plan validity.

    Args:
        db (AsyncSession): Async database session.
        now (datetime | None): Current datetime for comparison (default: datetime.now()).

    Returns:
        list[dict]: List of result dicts with autopay_id, status (success/failed), tx_id or error.
    """
    if now is None:
        now = datetime.now()

    due = await get_due_autopays(db, now=now)
    results = []

    for ap in due:
        # Build recharge request
        recharge_req = RechargeRequest(
            phone_number=ap.phone_number,
            plan_id=ap.plan_id,
            offer_id=None,
            payment_method=PaymentMethod.Wallet,
            source=TransactionSource.autopay,
            activation_mode="activate",
        )

        try:
            tx = await subscribe_plan(db=db, request=recharge_req, current_user=ap.user)
            results.append({"autopay_id": ap.autopay_id, "status": "success", "tx_id": tx.id})
        except Exception as exc:
            results.append({"autopay_id": ap.autopay_id, "status": "failed", "error": str(exc)})

        # Update next due date if regular
        if ap.tag == AutoPayTag.regular:
            # Example: add plan validity days
            plan = ap.plan
            if plan and plan.validity:
                ap.next_due_date = now + timedelta(days=plan.validity)
                db.add(ap)

    await db.commit()
    return results