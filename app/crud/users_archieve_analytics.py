from typing import List, Dict, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select, func, and_, cast, Numeric
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.users_archieve import UserArchieve

TZ = ZoneInfo("Asia/Kolkata")

def make_naive(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert aware datetime -> UTC naive for TIMESTAMP WITHOUT TIME ZONE columns."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    return dt

# totals
async def total_archived_users(db: AsyncSession) -> int:
    q = select(func.count()).select_from(UserArchieve)
    res = await db.execute(q)
    return int(res.scalar_one() or 0)

async def distribution_by_user_type(db: AsyncSession) -> List[Dict]:
    q = select(UserArchieve.user_type, func.count()).group_by(UserArchieve.user_type)
    res = await db.execute(q)
    return [{"key": (r[0].value if hasattr(r[0], "value") else r[0]), "count": int(r[1])} for r in res.all()]

async def distribution_by_status(db: AsyncSession) -> List[Dict]:
    q = select(UserArchieve.status, func.count()).group_by(UserArchieve.status)
    res = await db.execute(q)
    return [{"key": (r[0].value if hasattr(r[0], "value") else r[0]), "count": int(r[1])} for r in res.all()]

# period counts (deleted_at)
async def count_deleted_between(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> int:
    start_dt = make_naive(start_dt); end_dt = make_naive(end_dt)
    q = select(func.count()).where(and_(UserArchieve.deleted_at >= start_dt, UserArchieve.deleted_at <= end_dt))
    res = await db.execute(q)
    return int(res.scalar_one() or 0)

# trends by day (deleted_at)
async def deletion_trend_by_day(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    start_dt = make_naive(start_dt); end_dt = make_naive(end_dt)
    q = (
        select(func.date_trunc("day", UserArchieve.deleted_at).label("day"), func.count().label("cnt"))
        .where(UserArchieve.deleted_at >= start_dt, UserArchieve.deleted_at <= end_dt)
        .group_by("day").order_by("day")
    )
    res = await db.execute(q)
    rows = res.all()
    mapping = {r[0].date(): int(r[1]) for r in rows}
    out = []
    cur = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    last = end_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    while cur.date() <= last.date():
        out.append({"date": cur.date().isoformat(), "count": mapping.get(cur.date(), 0)})
        cur = cur + timedelta(days=1)
    return out

# trends by month (deleted_at)
async def deletion_trend_by_month(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    start_dt = make_naive(start_dt); end_dt = make_naive(end_dt)
    q = (
        select(func.date_trunc("month", UserArchieve.deleted_at).label("month"), func.count().label("cnt"))
        .where(UserArchieve.deleted_at >= start_dt, UserArchieve.deleted_at <= end_dt)
        .group_by("month").order_by("month")
    )
    res = await db.execute(q)
    rows = res.all()
    out = [{"month": r[0].date().isoformat(), "count": int(r[1])} for r in rows]
    return out

# avg / total wallet_balance
async def total_wallet_in_archive(db: AsyncSession) -> float:
    # wallet_balance is Numeric -> cast to Numeric and sum -> float
    q = select(func.coalesce(func.sum(cast(UserArchieve.wallet_balance, Numeric)), 0))
    res = await db.execute(q)
    val = res.scalar_one()
    return float(val or 0.0)

async def avg_wallet_balance(db: AsyncSession) -> float:
    q = select(func.coalesce(func.avg(cast(UserArchieve.wallet_balance, Numeric)), 0))
    res = await db.execute(q)
    val = res.scalar_one()
    return float(val or 0.0)

# top archived by wallet
async def top_by_wallet(db: AsyncSession, limit: int = 10) -> List[Dict]:
    q = (
        select(
            UserArchieve.user_id,
            UserArchieve.name,
            UserArchieve.email,
            UserArchieve.phone_number,
            UserArchieve.referral_code,
            UserArchieve.referee_code,
            cast(UserArchieve.wallet_balance, Numeric).label("wallet_balance"),
            UserArchieve.created_at,
            UserArchieve.deleted_at,
            UserArchieve.user_type,
            UserArchieve.status
        )
        .order_by(cast(UserArchieve.wallet_balance, Numeric).desc().nullslast())
        .limit(limit)
    )
    res = await db.execute(q)
    out = []
    for r in res.all():
        out.append({
            "user_id": int(r[0]),
            "name": r[1],
            "email": r[2],
            "phone_number": r[3],
            "referral_code": r[4],
            "referee_code": r[5],
            "wallet_balance": float(r[6]) if r[6] is not None else 0.0,
            "created_at": r[7],
            "deleted_at": r[8],
            "user_type": (r[9].value if hasattr(r[9], "value") else r[9]),
            "status": (r[10].value if hasattr(r[10], "value") else r[10]),
        })
    return out

# recent deletions (by deleted_at desc)
async def recent_deleted(db: AsyncSession, limit: int = 20) -> List[Dict]:
    q = (
        select(
            UserArchieve.user_id,
            UserArchieve.name,
            UserArchieve.email,
            UserArchieve.phone_number,
            UserArchieve.referral_code,
            UserArchieve.referee_code,
            cast(UserArchieve.wallet_balance, Numeric).label("wallet_balance"),
            UserArchieve.created_at,
            UserArchieve.deleted_at,
            UserArchieve.user_type,
            UserArchieve.status
        )
        .order_by(UserArchieve.deleted_at.desc().nullslast())
        .limit(limit)
    )
    res = await db.execute(q)
    out = []
    for r in res.all():
        out.append({
            "user_id": int(r[0]),
            "name": r[1],
            "email": r[2],
            "phone_number": r[3],
            "referral_code": r[4],
            "referee_code": r[5],
            "wallet_balance": float(r[6]) if r[6] is not None else 0.0,
            "created_at": r[7],
            "deleted_at": r[8],
            "user_type": (r[9].value if hasattr(r[9], "value") else r[9]),
            "status": (r[10].value if hasattr(r[10], "value") else r[10]),
        })
    return out

# phone duplicates
async def phone_number_duplicates(db: AsyncSession, min_count: int = 2) -> List[Dict]:
    q = select(UserArchieve.phone_number, func.count()).group_by(UserArchieve.phone_number).having(func.count() >= min_count).order_by(func.count().desc())
    res = await db.execute(q)
    return [{"phone_number": r[0], "count": int(r[1])} for r in res.all()]
