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
    """
    Create a new autopay record for a user.

    Validates that the referenced plan and user exist before creating the record.
    Converts enum values to their string representations and removes timezone info from dates.

    Args:
        db (AsyncSession): Async database session.
        obj_in (AutoPayCreate): Autopay creation schema with all required fields.
        user_id (int): ID of the user creating the autopay.

    Returns:
        AutoPay: The newly created autopay record.

    Raises:
        HTTPException: If plan or user referenced in obj_in is not found.
    """
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
    """
    Retrieve a specific autopay record by ID and verify it belongs to the user.

    Args:
        db (AsyncSession): Async database session.
        autopay_id (int): ID of the autopay record to retrieve.
        user_id (int): ID of the user who owns the autopay.

    Returns:
        Optional[AutoPay]: Autopay record if found and owned by user, None otherwise.
    """
    stmt = select(AutoPay).where(AutoPay.autopay_id == autopay_id, AutoPay.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_multi_by_user(
    db: AsyncSession,
    *,
    user_id: int,
    page: int = 0,
    size: int = 0,
    status: AutoPayStatus | None = None,
    tag: AutoPayTag | None = None,
    phone_number: str | None = None,
    sort: Literal["created_at_desc", "created_at_asc", "next_due_date_desc", "next_due_date_asc"] = "created_at_desc",
) -> tuple[Sequence[AutoPay], int]:
    """
    Retrieve paginated autopay records for a specific user with filtering and sorting.

    Args:
        db (AsyncSession): Async database session.
        user_id (int): ID of the user to retrieve autopays for.
        page (int): Page number for pagination (default: 1).
        size (int): Number of records per page (default: 20).
        status (Optional[AutoPayStatus]): Filter by autopay status.
        tag (Optional[AutoPayTag]): Filter by autopay tag.
        phone_number (Optional[str]): Filter by phone number (partial match).
        sort (str): Sort order option (default: "created_at_desc").

    Returns:
        tuple: Tuple of (list of AutoPay records, total count).
    """
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
    if page > 0 and size > 0:
        stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return rows, total


async def get_multi_all(
    db: AsyncSession,
    *,
    phone_number: str | None = None,
    page: int = 0,
    size: int = 0,
    status: AutoPayStatus | None = None,
    tag: AutoPayTag | None = None,
    sort: Literal["created_at_desc", "created_at_asc", "next_due_date_desc", "next_due_date_asc"] = "created_at_desc",
) -> tuple[Sequence[AutoPay], int]:
    """
    Retrieve all paginated autopay records across all users with filtering and sorting.

    Args:
        db (AsyncSession): Async database session.
        phone_number (Optional[str]): Filter by phone number (partial match).
        page (int): Page number for pagination (default: 1).
        size (int): Number of records per page (default: 20).
        status (Optional[AutoPayStatus]): Filter by autopay status.
        tag (Optional[AutoPayTag]): Filter by autopay tag.
        sort (str): Sort order option (default: "created_at_desc").

    Returns:
        tuple: Tuple of (list of AutoPay records, total count).
    """
    stmt = select(AutoPay)

    if status:
        stmt = stmt.where(AutoPay.status == status)
    if tag:
        stmt = stmt.where(AutoPay.tag == tag)
    if phone_number:
        stmt = stmt.where(AutoPay.phone_number.like(f"%{phone_number}%"))

    order_map = {
        "created_at_desc": AutoPay.created_at.desc(),
        "created_at_asc": AutoPay.created_at.asc(),
        "next_due_date_desc": AutoPay.next_due_date.desc(),
        "next_due_date_asc": AutoPay.next_due_date.asc(),
    }
    stmt = stmt.order_by(order_map[sort])

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    if page or size:
        stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return rows, total


async def update_autopay(
    db: AsyncSession, *, db_obj: AutoPay, obj_in: AutoPayUpdate
) -> AutoPay:
    """
    Update an existing autopay record with new values.

    Validates that the referenced plan and user exist before updating.
    Converts enum values to strings and removes timezone info from dates.

    Args:
        db (AsyncSession): Async database session.
        db_obj (AutoPay): The existing autopay record to update.
        obj_in (AutoPayUpdate): Schema containing fields to update.

    Returns:
        AutoPay: The updated autopay record.

    Raises:
        HTTPException: If plan or user referenced in obj_in is not found.
    """
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
    """
    Delete an autopay record from the database.

    Args:
        db (AsyncSession): Async database session.
        db_obj (AutoPay): The autopay record to delete.

    Returns:
        None
    """
    await db.delete(db_obj)
    await db.commit()


async def get_due_autopays(db: AsyncSession, now: datetime) -> Sequence[AutoPay]:
    """
    Retrieve all autopays that are currently due for processing.

    Returns enabled autopays where the next_due_date has passed and tag is regular.

    Args:
        db (AsyncSession): Async database session.
        now (datetime): Current timestamp to check against.

    Returns:
        Sequence[AutoPay]: List of autopays that are due for processing.
    """
    stmt = select(AutoPay).where(
        AutoPay.status == AutoPayStatus.enabled.value,
        AutoPay.next_due_date <= now,
        AutoPay.tag == AutoPayTag.regular.value,
    )
    result = await db.execute(stmt)
    return result.scalars().all()