# app/services/referral.py
from math import ceil
from sqlalchemy.ext.asyncio import AsyncSession

from ..crud.referrals import get_user_referral_rewards, get_all_referral_rewards
from ..schemas.referrals import (
    ReferralRewardOut,
    PaginatedReferralReward,
    ReferralRewardStatus,
)


async def get_my_referral_history(
    db: AsyncSession,
    *,
    current_user_id: int,
    page: int = 1,
    size: int = 20,
    status: ReferralRewardStatus | None = None,
    sort: str = "created_at_desc",
) -> PaginatedReferralReward:
    rows, total = await get_user_referral_rewards(
        db, user_id=current_user_id, page=page, size=size, status=status, sort=sort
    )
    return PaginatedReferralReward(
        items=[ReferralRewardOut.model_validate(r) for r in rows],
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if size else 0,
    )


async def get_all_referral_history(
    db: AsyncSession,
    *,
    page: int = 1,
    size: int = 20,
    status: ReferralRewardStatus | None = None,
    sort: str = "created_at_desc",
) -> PaginatedReferralReward:
    rows, total = await get_all_referral_rewards(
        db, page=page, size=size, status=status, sort=sort
    )
    return PaginatedReferralReward(
        items=[ReferralRewardOut.model_validate(r) for r in rows],
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if size else 0,
    )