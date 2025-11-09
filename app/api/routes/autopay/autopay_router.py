from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, Query, HTTPException, Security
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes
from ....models.users import User
from ....schemas.autopay import (
    AutoPayCreate,
    AutoPayUpdate,
    AutoPayOut,
    PaginatedAutoPay,
    AutoPayStatus,
    AutoPayTag,
)
from app.services.autopay import (
    create_user_autopay,
    get_user_autopay,
    list_user_autopays,
    update_user_autopay,
    delete_user_autopay,
    list_all_autopays,
    process_due_autopays,
)

router = APIRouter()


# ====================== USER ENDPOINTS ======================
@router.post("/create_autopay", response_model=AutoPayOut, status_code=201)
async def add_autopay(
    payload: AutoPayCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"])
):
    return await create_user_autopay(db, obj_in=payload, current_user_id=current_user.user_id)


@router.get("/get_autopay/{autopay_id}", response_model=AutoPayOut)
async def get_one_autopay(
    autopay_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"])
):
    return await get_user_autopay(db, autopay_id=autopay_id, current_user_id=current_user.user_id)


@router.get("/get_all_autopay", response_model=PaginatedAutoPay)
async def list_my_autopays(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: AutoPayStatus | None = None,
    phone_number: str | None = None,
    tag: AutoPayTag | None = None,
    sort: Literal[
        "created_at_desc",
        "created_at_asc",
        "next_due_date_desc",
        "next_due_date_asc",
    ] = "created_at_desc",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"])
):
    return await list_user_autopays(
        db,
        current_user_id=current_user.user_id,
        phone_number=phone_number,
        page=page,
        size=size,
        status=status,
        tag=tag,
        sort=sort,
    )


@router.patch("/{autopay_id}", response_model=AutoPayOut)
async def edit_autopay(
    autopay_id: int,
    payload: AutoPayUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"])
):
    return await update_user_autopay(
        db, autopay_id=autopay_id, obj_in=payload, current_user_id=current_user.user_id
    )


@router.delete("/{autopay_id}", status_code=204)
async def remove_autopay(
    autopay_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"])
):
    await delete_user_autopay(db, autopay_id=autopay_id, current_user_id=current_user.user_id)
    return None


# ====================== ADMIN ENDPOINTS ======================
@router.get("/admin/all", response_model=PaginatedAutoPay)
async def admin_list_all(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: AutoPayStatus | None = None,
    tag: AutoPayTag | None = None,
    phone_number: str | None = None,
    sort: Literal[
        "created_at_desc",
        "created_at_asc",
        "next_due_date_desc",
        "next_due_date_asc",
    ] = "created_at_desc",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Autopay:read"])
):
    return await list_all_autopays(
        db, page=page, size=size, status=status, tag=tag, sort=sort, phone_number=phone_number
    )


@router.post("/admin/process-due", response_model=list[dict])
async def admin_process_due(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Autopay:write"])
):
    """
    Executes all **regular** autopays whose `next_due_date <= now`.
    Returns success/failure per autopay.
    """
    return await process_due_autopays(db)