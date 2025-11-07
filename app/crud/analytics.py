from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
from datetime import datetime, timedelta
from ..models.users import User
from ..models.admins import Admin
from ..utils.analytics import start_of_day, make_naive
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Kolkata")

# Users crud
async def crud_total_users(db: AsyncSession) -> int:
    q = select(func.count()).select_from(User)
    res = await db.execute(q)
    return int(res.scalar_one())

async def crud_count_users_between(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> int:
    start_dt = make_naive(start_dt)
    end_dt = make_naive(end_dt)
    q = select(func.count()).select_from(User).where(
        and_(
            User.created_at >= start_dt,
            User.created_at <= end_dt
        )
    )
    res = await db.execute(q)
    return int(res.scalar_one())

async def crud_count_users_by_status(db: AsyncSession) -> List[Dict]:
    q = select(User.status, func.count()).group_by(User.status)
    res = await db.execute(q)
    rows = res.all()
    return [{"status": r[0].value if r[0] else None, "count": int(r[1])} for r in rows]

async def crud_count_users_by_type(db: AsyncSession) -> List[Dict]:
    q = select(User.user_type, func.count()).group_by(User.user_type)
    res = await db.execute(q)
    return [{"type": r[0].value if r[0] else None, "count": int(r[1])} for r in res.all()]

async def crud_avg_wallet_balance(db: AsyncSession) -> float:
    q = select(func.coalesce(func.avg(User.wallet_balance), 0))
    res = await db.execute(q)
    return float(res.scalar_one() or 0.0)

async def crud_users_trend_by_day(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    """
    Returns a list of {'date': 'YYYY-MM-DD', 'count': N} for each day in range.
    Uses date_trunc('day', created_at) grouping (Postgres).
    """
    start_dt = make_naive(start_dt)
    end_dt = make_naive(end_dt)
    q = (
        select(func.date_trunc("day", User.created_at).label("day"), func.count().label("cnt"))
        .where(User.created_at >= start_dt, User.created_at <= end_dt)
        .group_by("day")
        .order_by("day")
    )
    res = await db.execute(q)
    rows = res.all()
    out = []
    # build dict mapping full range to include zeros
    current = start_dt
    last = end_dt
    # normalize to date boundaries
    current = start_of_day(current)
    last = start_of_day(last)
    mapping = {r[0].date(): int(r[1]) for r in rows}
    while current.date() <= last.date():
        out.append({"date": current.date().isoformat(), "count": mapping.get(current.date(), 0)})
        current = current + timedelta(days=1)
    return out

async def crud_users_trend_by_month(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    start_dt = make_naive(start_dt)
    end_dt = make_naive(end_dt)
    q = (
        select(func.date_trunc("month", User.created_at).label("month"), func.count().label("cnt"))
        .where(User.created_at >= start_dt, User.created_at <= end_dt)
        .group_by("month")
        .order_by("month")
    )
    res = await db.execute(q)
    rows = res.all()
    out = []
    # produce list between months: iterate month-by-month
    from datetime import date
    def add_month(d):
        y = d.year + (d.month // 12)
        m = d.month % 12 + 1
        return datetime(y, m, 1, tzinfo=TZ)
    start_month = datetime(start_dt.year, start_dt.month, 1, tzinfo=TZ)
    end_month = datetime(end_dt.year, end_dt.month, 1, tzinfo=TZ)
    mapping = {r[0].date().replace(day=1): int(r[1]) for r in rows}  # r[0] is datetime truncated to month
    cur = start_month
    while cur.date() <= end_month.date():
        key = cur.date().replace(day=1)
        out.append({"month": key.isoformat(), "count": mapping.get(key, 0)})
        cur = add_month(cur)
    return out

async def crud_top_referrers(db: AsyncSession, limit: int = 10) -> List[Dict]:
    """
    Count how many referred users each user (by referral_code) has produced.
    This assumes ReferralReward or referred users have referee_code linking to referrer's referral_code.
    We'll join Users -> Users (self-join) to count how many users were referred by each referral_code.
    """
    # self-join: count referred rows per referral_code (referral_code in Users refers to referrer)
    referred = User.__table__.alias("referred")
    referrer = User.__table__.alias("referrer")
    q = (
        select(referrer.c.user_id.label("referrer_id"),
               referrer.c.name.label("referrer_name"),
               func.count(referred.c.user_id).label("referred_count"))
        .select_from(referrer.join(referred, referrer.c.referral_code == referred.c.referee_code))
        .group_by(referrer.c.user_id, referrer.c.name)
        .order_by(func.count(referred.c.user_id).desc())
        .limit(limit)
    )
    res = await db.execute(q)
    return [{"referrer_id": r[0], "referrer_name": r[1], "referred_count": int(r[2])} for r in res.all()]


# Admins Crud
async def total_admins(db: AsyncSession) -> int:
    q = select(func.count()).select_from(Admin)
    res = await db.execute(q)
    return int(res.scalar_one() or 0)

async def count_admins_between(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> int:
    start_dt = make_naive(start_dt)
    end_dt = make_naive(end_dt)
    q = select(func.count()).select_from(Admin).where(
        and_(Admin.created_at >= start_dt, Admin.created_at <= end_dt)
    )
    res = await db.execute(q)
    return int(res.scalar_one() or 0)

async def admins_by_role(db: AsyncSession) -> List[Dict]:
    q = select(Admin.role_id, func.count()).group_by(Admin.role_id)
    res = await db.execute(q)
    return [{"role_id": r[0], "count": int(r[1])} for r in res.all()]

async def admins_trend_by_month(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    start_dt = make_naive(start_dt)
    end_dt = make_naive(end_dt)
    q = (
        select(func.date_trunc("month", Admin.created_at).label("month"), func.count().label("cnt"))
        .where(Admin.created_at >= start_dt, Admin.created_at <= end_dt)
        .group_by("month").order_by("month")
    )
    res = await db.execute(q)
    rows = res.all()
    mapping = {r[0].date().replace(day=1): int(r[1]) for r in rows}
    out = []
    cur = datetime(start_dt.year, start_dt.month, 1, tzinfo=TZ)
    last = datetime(end_dt.year, end_dt.month, 1, tzinfo=TZ)
    def next_month(d):
        y = d.year + (d.month // 12)
        m = d.month % 12 + 1
        return datetime(y, m, 1, tzinfo=TZ)
    while cur.date() <= last.date():
        key = cur.date().replace(day=1)
        out.append({"month": key.isoformat(), "count": mapping.get(key, 0)})
        cur = next_month(cur)
    return out
