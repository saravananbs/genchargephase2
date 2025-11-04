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
    AutoPayStatus,
    AutoPayTag,
)
from fastapi import HTTPException
from starlette import status
from ..services.recharge import subscribe_plan, RechargeRequest, TransactionSource, PaymentMethod


async def create_user_autopay(
    db: AsyncSession, *, obj_in: AutoPayCreate, current_user_id: int
) -> AutoPayOut:
    autopay = await create_autopay(db, obj_in=obj_in, user_id=current_user_id)
    return AutoPayOut.model_validate(autopay)


async def get_user_autopay(
    db: AsyncSession, *, autopay_id: int, current_user_id: int
) -> AutoPayOut:
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
    page: int = 1,
    size: int = 20,
    status: AutoPayStatus | None = None,
    tag: AutoPayTag | None = None,
    sort: str = "created_at_desc",
    phone_number: str | None = None
) -> PaginatedAutoPay:
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
    page: int = 1,
    size: int = 20,
    phone_number: str | None = None,
    status: AutoPayStatus | None = None,
    tag: AutoPayTag | None = None,
    sort: str = "created_at_desc",
) -> PaginatedAutoPay:
    rows, total = await get_multi_all(
        db, page=page, size=size, status=status, tag=tag, sort=sort
    )
    return PaginatedAutoPay(
        items=[AutoPayOut.model_validate(r) for r in rows],
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if size else 0,
    )


async def process_due_autopays(db: AsyncSession, now: datetime | None = None) -> list[dict]:
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