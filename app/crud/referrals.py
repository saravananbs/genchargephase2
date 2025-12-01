# app/crud/referral.py
from typing import Sequence, Literal, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.referral import ReferralReward
from ..schemas.referrals import ReferralRewardStatus
from datetime import datetime
from ..models.users import User


async def get_user_referral_rewards(
    db: AsyncSession,
    *,
    user_id: int,
    page: int = 0,
    size: int = 0,
    status: ReferralRewardStatus | None = None,
    sort: Literal[
        "created_at_desc", "created_at_asc",
        "reward_amount_desc", "reward_amount_asc"
    ] = "created_at_desc",
) -> tuple[Sequence[ReferralReward], int]:
    """
    Return referral rewards for a given user (either as referrer or referred).

    Supports paging and optional filtering by status and sorting.

    Args:
        db (AsyncSession): Async database session.
        user_id (int): User ID to lookup rewards for.
        page (int): Page number (1-based).
        size (int): Page size.
        status (Optional[ReferralRewardStatus]): Optional status filter.
        sort (str): Sort key from the allowed set.

    Returns:
        tuple[Sequence[ReferralReward], int]: (list of rewards, total count).
    """
    base_stmt = select(ReferralReward).where(
        (ReferralReward.referrer_id == user_id)
    )

    if status:
        base_stmt = base_stmt.where(ReferralReward.status == status.value)

    order_map = {
        "created_at_desc": ReferralReward.created_at.desc(),
        "created_at_asc": ReferralReward.created_at.asc(),
        "reward_amount_desc": ReferralReward.reward_amount.desc(),
        "reward_amount_asc": ReferralReward.reward_amount.asc(),
    }
    order_clause = order_map[sort]

    count_stmt = select(func.count()).select_from(
        base_stmt.order_by(None).subquery()
    )
    total = (await db.execute(count_stmt)).scalar_one()

    data_stmt = base_stmt.options(
        selectinload(ReferralReward.referred)
    ).order_by(order_clause)

    if page or size:
        data_stmt = data_stmt.offset((page - 1) * size).limit(size)

    result = await db.execute(data_stmt)
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
    """
    Return all referral rewards (admin view) with optional paging, status filter and sorting.

    Args:
        db (AsyncSession): Async database session.
        page (int): Page number (1-based).
        size (int): Page size.
        status (Optional[ReferralRewardStatus]): Optional status filter.
        sort (str): Sort key from the allowed set.

    Returns:
        tuple[Sequence[ReferralReward], int]: (list of rewards, total count).
    """
    base_stmt = select(ReferralReward)

    if status:
        base_stmt = base_stmt.where(ReferralReward.status == status.value)

    order_map = {
        "created_at_desc": ReferralReward.created_at.desc(),
        "created_at_asc": ReferralReward.created_at.asc(),
        "reward_amount_desc": ReferralReward.reward_amount.desc(),
        "reward_amount_asc": ReferralReward.reward_amount.asc(),
    }
    order_clause = order_map[sort]

    count_stmt = select(func.count()).select_from(
        base_stmt.order_by(None).subquery()
    )
    total = (await db.execute(count_stmt)).scalar_one()

    data_stmt = base_stmt.options(
        selectinload(ReferralReward.referred)
    ).order_by(order_clause)

    data_stmt = data_stmt.offset((page - 1) * size).limit(size)

    result = await db.execute(data_stmt)
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
    Attempt to claim a referral reward when eligibility conditions are met.

    Conditions (evaluated in order):
      - Both users must be active.
      - The referred user's referee_code must match the referrer's referral_code.
      - No previously earned reward exists for this pair.

    If eligible, marks the reward as earned, credits the referrer's wallet and returns
    the updated ReferralReward. If not eligible, returns None.

    Args:
        db (AsyncSession): Async database session.
        referrer (User): Referrer user instance.
        referred (User): Referred user instance.
        reward_amount (Optional[float]): Reward amount to apply (defaults to 50).

    Returns:
        Optional[ReferralReward]: Updated reward if claimed, otherwise None.
    """
    if reward_amount is None:
        reward_amount = 50  # e.g. 50.00

    # --- 1. Validate users ---
    if referrer and str(referrer.status) != "UserStatus.active" or str(referred.status) != "UserStatus.active":
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