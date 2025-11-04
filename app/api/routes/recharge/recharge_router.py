from fastapi import APIRouter, Depends, HTTPException, status, Query, Security
from typing import List, Optional, Literal
from sqlalchemy.ext.asyncio import AsyncSession

from ....models.users import User
from ....core.database import get_db
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes
from ....schemas.recharge import (
    RechargeRequest,
    WalletTopupRequest,
    TransactionOut,
    CurrentActivePlanOut,
    CurrentPlanListResponse,
    TransactionListResponse,
    CurrentPlanFilterParams,
    TransactionFilterParams,
    UserCurrentPlanFilterParams,
    UserTransactionFilterParams
)
from ....models.current_active_plans import CurrentPlanStatus
from ....models.transactions import TransactionCategory, TransactionType, TransactionStatus
from ....services.recharge import (
    subscribe_plan,
    wallet_topup,
    get_my_active_plans,
    get_my_transactions,
    admin_list_active_plans,
    admin_list_transactions,
)

router = APIRouter()


# ====================== USER ENDPOINTS ======================
@router.post("/subscribe", response_model=TransactionOut)
async def subscribe(
    request: RechargeRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    _=Security(require_scopes, scopes=["User"]),
):
    try:
        return await subscribe_plan(db, request, current_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/wallet/topup", response_model=TransactionOut)
async def topup(
    request: WalletTopupRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    _=Security(require_scopes, scopes=["User"]),
):
    try:
        return await wallet_topup(db, request, current_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my/plans", response_model=CurrentPlanListResponse)
async def my_plans(
    filters: UserCurrentPlanFilterParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ = Security(require_scopes, scopes=["User"]),
):
    """
    * `sort_by` – `valid_from` or `valid_to`  
    * `sort_order` – `asc` or `desc` (default `desc`)
    """
    res = CurrentPlanFilterParams(**filters.model_dump())
    res.phone_number = current_user.phone_number
    return await admin_list_active_plans(db, res)

@router.get("/my/transactions", response_model=TransactionListResponse)
async def my_transactions(
    f: UserTransactionFilterParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ = Security(require_scopes, scopes=["User"]),
):
    """
    Returns a paginated list of **Transaction** with **all** requested filters.

    * `size=0` → return **every** matching row (no pagination).  
    * All enum fields appear as **dropdowns** in Swagger.  
    * Date fields use the **date picker**.  
    """
    res = TransactionFilterParams(**f.model_dump())
    res.from_phone_number = current_user.phone_number
    return await admin_list_transactions(db, res)


# ====================== ADMIN ENDPOINTS ======================
@router.get("/admin/active-plans",response_model=CurrentPlanListResponse)
async def admin_active_plans(
    filters: CurrentPlanFilterParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Security(require_scopes, scopes=["Recharge:read"]),
):
    """
    * `sort_by` – `valid_from` or `valid_to`  
    * `sort_order` – `asc` or `desc` (default `desc`)
    """
    return await admin_list_active_plans(db, filters)

@router.get("/admin/transactions", response_model=TransactionListResponse)
async def admin_transactions(
    f: TransactionFilterParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Security(require_scopes, scopes=["Recharge:read"]),
):
    """
    Returns a paginated list of **Transaction** with **all** requested filters.

    * `size=0` → return **every** matching row (no pagination).  
    * All enum fields appear as **dropdowns** in Swagger.  
    * Date fields use the **date picker**.  
    """
    return await admin_list_transactions(db, f)