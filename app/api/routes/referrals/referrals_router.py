# app/api/v1/endpoints/referral.py
from fastapi import APIRouter, Depends, Query, Security
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal

from ....core.database import get_db
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes
from ....models.users import User
from ....schemas.referrals import (
    PaginatedReferralReward,
    ReferralRewardStatus,
)
from app.services.referral import get_my_referral_history, get_all_referral_history

router = APIRouter()


@router.get("/me", response_model=PaginatedReferralReward)
async def my_referral_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: ReferralRewardStatus | None = None,
    sort: Literal[
        "created_at_desc", "created_at_asc",
        "reward_amount_desc", "reward_amount_asc"
    ] = "created_at_desc",
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"], use_cache=False)
):
    """View your own referral earnings (as referrer OR referred)"""
    return await get_my_referral_history(
        db,
        current_user_id=current_user.user_id,
        page=page,
        size=size,
        status=status,
        sort=sort,
    )


@router.get("/admin/all", response_model=PaginatedReferralReward)
async def admin_referral_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: ReferralRewardStatus | None = None,
    sort: Literal[
        "created_at_desc", "created_at_asc",
        "reward_amount_desc", "reward_amount_asc"
    ] = "created_at_desc",
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Referral:read"], use_cache=False)
):
    """Admin: View all referral rewards in the system"""
    return await get_all_referral_history(
        db, page=page, size=size, status=status, sort=sort
    )