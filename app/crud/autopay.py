# app/crud/autopay.py
from typing import Sequence, Literal
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from datetime import datetime
from fastapi import HTTPException
from starlette import status

from ..models.autopay import AutoPay, AutoPayStatus, AutoPayTag
from ..schemas.autopay import AutoPayCreate, AutoPayUpdate
from ..crud.plans import get_plan_by_id
from ..crud.users import get_user_by_phone


async def create_autopay(
    db: AsyncSession, *, obj_in: AutoPayCreate, user_id: int
) -> AutoPay:
    data = obj_in.model_dump()
    data["status"] = data["status"].value
    data["tag"] = data["tag"].value
    if data["next_due_date"].tzinfo is not None:
        data["next_due_date"] = data["next_due_date"].replace(tzinfo=None)
    plan = await get_plan_by_id(db, plan_id=obj_in.plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan with id {obj_in.plan_id} not found",
            headers={"X-Error": "Item not found in database"},
        )
    user = await get_user_by_phone(db, obj_in.phone_number)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with number {obj_in.phone_number} not found",
            headers={"X-Error": "Item not found in database"},
        )
    db_obj = AutoPay(**data, user_id=user_id)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def get_autopay(db: AsyncSession, *, autopay_id: int, user_id: int) -> AutoPay | None:
    stmt = select(AutoPay).where(AutoPay.autopay_id == autopay_id, AutoPay.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_multi_by_user(
    db: AsyncSession,
    *,
    user_id: int,
    page: int = 1,
    size: int = 20,
    status: AutoPayStatus | None = None,
    tag: AutoPayTag | None = None,
    phone_number: str | None = None,
    sort: Literal["created_at_desc", "created_at_asc", "next_due_date_desc", "next_due_date_asc"] = "created_at_desc",
) -> tuple[Sequence[AutoPay], int]:
    # Base query
    stmt = select(AutoPay).where(AutoPay.user_id == user_id)

    # Filters
    if status:
        stmt = stmt.where(AutoPay.status == status)
    if tag:
        stmt = stmt.where(AutoPay.tag == tag)
    if phone_number:
        stmt = stmt.where(AutoPay.phone_number.like(f"%{phone_number}%"))

    # Sorting
    order_map = {
        "created_at_desc": AutoPay.created_at.desc(),
        "created_at_asc": AutoPay.created_at.asc(),
        "next_due_date_desc": AutoPay.next_due_date.desc(),
        "next_due_date_asc": AutoPay.next_due_date.asc(),
    }
    stmt = stmt.order_by(order_map[sort])

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    # Pagination
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return rows, total


async def get_multi_all(
    db: AsyncSession,
    *,
    phone_number: str | None = None,
    page: int = 1,
    size: int = 20,
    status: AutoPayStatus | None = None,
    tag: AutoPayTag | None = None,
    sort: Literal["created_at_desc", "created_at_asc", "next_due_date_desc", "next_due_date_asc"] = "created_at_desc",
) -> tuple[Sequence[AutoPay], int]:
    stmt = select(AutoPay)

    if status:
        stmt = stmt.where(AutoPay.status == status)
    if tag:
        stmt = stmt.where(AutoPay.tag == tag)
    if phone_number:
        stmt = stmt.where(AutoPay.phone_number.like(f"{phone_number}"))

    order_map = {
        "created_at_desc": AutoPay.created_at.desc(),
        "created_at_asc": AutoPay.created_at.asc(),
        "next_due_date_desc": AutoPay.next_due_date.desc(),
        "next_due_date_asc": AutoPay.next_due_date.asc(),
    }
    stmt = stmt.order_by(order_map[sort])

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return rows, total


async def update_autopay(
    db: AsyncSession, *, db_obj: AutoPay, obj_in: AutoPayUpdate
) -> AutoPay:
    update_data = obj_in.model_dump(exclude_unset=True)
    if "status" in update_data:
        update_data["status"] = update_data["status"].value
    if "tag" in update_data:
        update_data["tag"] = update_data["tag"].value

    # --- FIX: Strip timezone if updating next_due_date ---
    if "next_due_date" in update_data and update_data["next_due_date"].tzinfo is not None:
        update_data["next_due_date"] = update_data["next_due_date"].replace(tzinfo=None)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    plan = await get_plan_by_id(db, plan_id=obj_in.plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan with id {obj_in.plan_id} not found",
            headers={"X-Error": "Item not found in database"},
        )
    user = await get_user_by_phone(db, obj_in.phone_number)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with number {obj_in.phone_number} not found",
            headers={"X-Error": "Item not found in database"},
        )
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_autopay(db: AsyncSession, *, db_obj: AutoPay) -> None:
    await db.delete(db_obj)
    await db.commit()


async def get_due_autopays(db: AsyncSession, now: datetime) -> Sequence[AutoPay]:
    stmt = select(AutoPay).where(
        AutoPay.status == AutoPayStatus.enabled.value,
        AutoPay.next_due_date <= now,
        AutoPay.tag == AutoPayTag.regular.value,
    )
    result = await db.execute(stmt)
    return result.scalars().all()