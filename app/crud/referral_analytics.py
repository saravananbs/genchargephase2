# app/crud/crud_referrals.py
from typing import List, Dict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select, func, and_, case, Numeric
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.referral import ReferralReward

TZ = ZoneInfo("Asia/Kolkata")

def make_naive(dt: datetime):
    """
    Convert timezone-aware datetime to UTC-naive datetime.

    Args:
        dt (datetime): Datetime object to convert.

    Returns:
        datetime: UTC-naive datetime.
    """
    if dt.tzinfo is not None:
        return dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    return dt

# ---------- BASIC AGGREGATES ----------
async def total_rewards(db: AsyncSession) -> int:
    """
    Get total count of all referral reward records.

    Args:
        db (AsyncSession): Async database session.

    Returns:
        int: Total number of referral rewards.
    """
    q = select(func.count()).select_from(ReferralReward)
    res = await db.execute(q)
    return int(res.scalar_one() or 0)

async def total_reward_amount(db: AsyncSession) -> float:
    """
    Get total reward amount across all referral rewards.

    Args:
        db (AsyncSession): Async database session.

    Returns:
        float: Sum of all reward amounts.
    """
    q = select(func.coalesce(func.sum(ReferralReward.reward_amount), 0))
    res = await db.execute(q)
    return float(res.scalar_one() or 0.0)

async def total_by_status(db: AsyncSession) -> List[Dict]:
    """
    Get distribution of referral rewards grouped by status with total amounts.

    Args:
        db (AsyncSession): Async database session.

    Returns:
        List[Dict]: List of dictionaries with 'status', 'count', and 'total_amount' fields.
    """
    q = select(ReferralReward.status, func.count(), func.sum(ReferralReward.reward_amount)).group_by(ReferralReward.status)
    res = await db.execute(q)
    return [
        {"status": r[0], "count": int(r[1]), "total_amount": float(r[2] or 0.0)}
        for r in res.all()
    ]

# ---------- PERIOD QUERIES ----------
async def count_and_amount_between(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> Dict:
    """
    Get count and total reward amount for rewards created within a date range.

    Args:
        db (AsyncSession): Async database session.
        start_dt (datetime): Start of the date range (inclusive).
        end_dt (datetime): End of the date range (inclusive).

    Returns:
        Dict: Dictionary with 'count' and 'total_amount' fields.
    """
    start_dt = make_naive(start_dt)
    end_dt = make_naive(end_dt)
    q = select(
        func.count(),
        func.coalesce(func.sum(ReferralReward.reward_amount), 0)
    ).where(and_(ReferralReward.created_at >= start_dt, ReferralReward.created_at <= end_dt))
    res = await db.execute(q)
    row = res.first()
    return {"count": int(row[0] or 0), "total_amount": float(row[1] or 0)}

async def count_claimed_between(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> int:
    """
    Count claimed referral rewards within a date range.

    Args:
        db (AsyncSession): Async database session.
        start_dt (datetime): Start of the date range (inclusive).
        end_dt (datetime): End of the date range (inclusive).

    Returns:
        int: Number of claimed rewards in the date range.
    """
    start_dt = make_naive(start_dt)
    end_dt = make_naive(end_dt)
    q = select(func.count()).where(and_(ReferralReward.claimed_at >= start_dt, ReferralReward.claimed_at <= end_dt))
    res = await db.execute(q)
    return int(res.scalar_one() or 0)

# ---------- TRENDS ----------
async def trend_by_day(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    """
    Get daily trend of referral rewards created within a date range.

    Ensures all days in range are represented, even if they have zero rewards.

    Args:
        db (AsyncSession): Async database session.
        start_dt (datetime): Start of the date range (inclusive).
        end_dt (datetime): End of the date range (inclusive).

    Returns:
        List[Dict]: List of dictionaries with 'date', 'count', and 'total_amount' fields.
    """
    start_dt = make_naive(start_dt)
    end_dt = make_naive(end_dt)
    q = (
        select(
            func.date_trunc("day", ReferralReward.created_at).label("day"),
            func.count().label("cnt"),
            func.coalesce(func.sum(ReferralReward.reward_amount), 0).label("amt")
        )
        .where(ReferralReward.created_at >= start_dt, ReferralReward.created_at <= end_dt)
        .group_by("day").order_by("day")
    )
    res = await db.execute(q)
    rows = res.all()
    mapping = {r[0].date(): {"count": int(r[1]), "amt": float(r[2] or 0)} for r in rows}
    out = []
    cur = start_dt
    while cur.date() <= end_dt.date():
        m = mapping.get(cur.date(), {"count": 0, "amt": 0})
        out.append({"date": cur.date().isoformat(), "count": m["count"], "total_amount": m["amt"]})
        cur += timedelta(days=1)
    return out

async def trend_by_month(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    """
    Get monthly trend of referral rewards created within a date range.

    Args:
        db (AsyncSession): Async database session.
        start_dt (datetime): Start of the date range (inclusive).
        end_dt (datetime): End of the date range (inclusive).

    Returns:
        List[Dict]: List of dictionaries with 'month', 'count', and 'total_amount' fields.
    """
    start_dt = make_naive(start_dt)
    end_dt = make_naive(end_dt)
    q = (
        select(
            func.date_trunc("month", ReferralReward.created_at).label("month"),
            func.count().label("cnt"),
            func.coalesce(func.sum(ReferralReward.reward_amount), 0).label("amt")
        )
        .where(ReferralReward.created_at >= start_dt, ReferralReward.created_at <= end_dt)
        .group_by("month").order_by("month")
    )
    res = await db.execute(q)
    rows = res.all()
    out = [
        {"month": r[0].date().isoformat(), "count": int(r[1]), "total_amount": float(r[2] or 0)}
        for r in rows
    ]
    return out

# ---------- DISTRIBUTIONS ----------
async def distribution_by_amount_range(db: AsyncSession) -> List[Dict]:
    """
    Create distribution of referral rewards grouped into amount buckets.

    Args:
        db (AsyncSession): Async database session.

    Returns:
        List[Dict]: List of dictionaries with 'key' (range) and 'count' fields.
    """
    buckets = case(
        (
            ReferralReward.reward_amount < 10, "0-10"
        ),
        (
            and_(ReferralReward.reward_amount >= 10, ReferralReward.reward_amount < 50), "10-50"
        ),
        else_="50+"
    )
    q = select(buckets.label("range"), func.count()).group_by("range")
    res = await db.execute(q)
    return [{"key": r[0], "count": int(r[1])} for r in res.all()]

async def top_referrers(db: AsyncSession, limit: int = 10) -> List[Dict]:
    """
    Get top referrers by total reward amount.

    Args:
        db (AsyncSession): Async database session.
        limit (int): Maximum number of referrers to return (default: 10).

    Returns:
        List[Dict]: List of dictionaries with 'referrer_id', 'total_rewards', and 'total_amount' fields.
    """
    q = select(
        ReferralReward.referrer_id,
        func.count().label("count"),
        func.sum(ReferralReward.reward_amount).label("total")
    ).group_by(ReferralReward.referrer_id).order_by(func.sum(ReferralReward.reward_amount).desc()).limit(limit)
    res = await db.execute(q)
    return [{"referrer_id": r[0], "total_rewards": int(r[1]), "total_amount": float(r[2] or 0.0)} for r in res.all()]

# ---------- AVERAGES ----------
async def avg_reward_amount(db: AsyncSession) -> float:
    """
    Get average reward amount across all referral rewards.

    Args:
        db (AsyncSession): Async database session.

    Returns:
        float: Average reward amount.
    """
    q = select(func.coalesce(func.avg(ReferralReward.reward_amount), 0))
    res = await db.execute(q)
    val = res.scalar_one()
    return float(val or 0.0)

async def avg_claim_time_days(db: AsyncSession) -> float:
    """
    Get average time in days between reward creation and claim.

    Args:
        db (AsyncSession): Async database session.

    Returns:
        float: Average claim time in days, rounded to 2 decimal places.
    """
    q = select(
        func.coalesce(func.avg(func.extract("epoch", ReferralReward.claimed_at - ReferralReward.created_at)), 0)
    )
    res = await db.execute(q)
    val = res.scalar_one()
    return round(float(val) / 86400.0, 2) if val else 0.0
