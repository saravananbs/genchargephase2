# app/crud/referral.py
from typing import Sequence, Literal, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from math import ceil

from ..models.referral import ReferralReward
from ..schemas.referrals import ReferralRewardStatus
from datetime import datetime
from ..models.users import User


async def get_user_referral_rewards(
    db: AsyncSession,
    *,
    user_id: int,
    page: int = 1,
    size: int = 20,
    status: ReferralRewardStatus | None = None,
    sort: Literal[
        "created_at_desc", "created_at_asc",
        "reward_amount_desc", "reward_amount_asc"
    ] = "created_at_desc",
) -> tuple[Sequence[ReferralReward], int]:
    stmt = select(ReferralReward).where(
        (ReferralReward.referrer_id == user_id) |
        (ReferralReward.referred_id == user_id)
    )

    if status:
        stmt = stmt.where(ReferralReward.status == status.value)

    order_map = {
        "created_at_desc": ReferralReward.created_at.desc(),
        "created_at_asc": ReferralReward.created_at.asc(),
        "reward_amount_desc": ReferralReward.reward_amount.desc(),
        "reward_amount_asc": ReferralReward.reward_amount.asc(),
    }
    stmt = stmt.order_by(order_map[sort])

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return rows, total


async def get_all_referral_rewards(
    db: AsyncSession,
    *,
    page: int = 1,
    size: int = 20,
    status: ReferralRewardStatus | None = None,
    sort: Literal[
        "created_at_desc", "created_at_asc",
        "reward_amount_desc", "reward_amount_asc"
    ] = "created_at_desc",
) -> tuple[Sequence[ReferralReward], int]:
    stmt = select(ReferralReward)

    if status:
        stmt = stmt.where(ReferralReward.status == status.value)

    order_map = {
        "created_at_desc": ReferralReward.created_at.desc(),
        "created_at_asc": ReferralReward.created_at.asc(),
        "reward_amount_desc": ReferralReward.reward_amount.desc(),
        "reward_amount_asc": ReferralReward.reward_amount.asc(),
    }
    stmt = stmt.order_by(order_map[sort])

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return rows, total

async def claim_referral_if_eligible(
    db: AsyncSession,
    *,
    referrer: User,
    referred: User,
    reward_amount: Optional[float] = None,
) -> ReferralReward | None:
    """
    Claim referral reward if:
    - No reward exists OR only 'pending' exists
    - Both users are active
    - Referred user has referee_code set

    Returns ReferralReward if created, else None.
    """
    if reward_amount is None:
        reward_amount = 50  # e.g. 50.00

    # --- 1. Validate users ---
    if str(referrer.status) != "UserStatus.active" or str(referred.status) != "UserStatus.active":
        print("non active")
        return None
    
    if not referred.referee_code or referred.referee_code != referrer.referral_code:
        print("not equal")
        return None

    # --- 2. Check if reward already exists and is claimed ---
    stmt = select(ReferralReward).where(
        ReferralReward.referrer_id == referrer.user_id,
        ReferralReward.referred_id == referred.user_id,
    ).order_by(ReferralReward.created_at.desc())

    result = await db.execute(stmt)
    existing = result.scalars().first()

    if existing:
        if existing.status in (ReferralRewardStatus.earned.value):
            print("failed")
            return None 

    # --- 3. Create new pending reward ---
    existing.claimed_at = datetime.now()
    existing.status = ReferralRewardStatus.earned.value
    referrer.wallet_balance += 50
    await db.commit()
    await db.refresh(existing)
    return existing