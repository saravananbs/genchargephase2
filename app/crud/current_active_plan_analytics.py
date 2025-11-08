# crud_current_active_plans.py
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select, func, and_, cast, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.current_active_plans import CurrentActivePlan

TZ = ZoneInfo("Asia/Kolkata")

def make_naive(dt: datetime) -> datetime:
    """Convert tz-aware -> UTC-naive for TIMESTAMP WITHOUT TIME ZONE columns.
    If dt is already naive, returns as-is."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    return dt

async def total_active_plans(db: AsyncSession) -> int:
    q = select(func.count()).select_from(CurrentActivePlan)
    res = await db.execute(q)
    return int(res.scalar_one() or 0)

async def count_by_status(db: AsyncSession) -> List[Dict]:
    q = select(CurrentActivePlan.status, func.count()).group_by(CurrentActivePlan.status)
    res = await db.execute(q)
    return [{"status": r[0].value if hasattr(r[0], "value") else r[0], "count": int(r[1])} for r in res.all()]

async def count_by_plan(db: AsyncSession) -> List[Dict]:
    q = select(CurrentActivePlan.plan_id, func.count()).group_by(CurrentActivePlan.plan_id).order_by(func.count().desc())
    res = await db.execute(q)
    return [{"plan_id": int(r[0]) if r[0] is not None else None, "count": int(r[1])} for r in res.all()]

async def count_activations_between(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> int:
    start_dt = make_naive(start_dt); end_dt = make_naive(end_dt)
    q = select(func.count()).where(and_(CurrentActivePlan.valid_from >= start_dt, CurrentActivePlan.valid_from <= end_dt))
    res = await db.execute(q)
    return int(res.scalar_one() or 0)

async def count_expirations_between(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> int:
    start_dt = make_naive(start_dt); end_dt = make_naive(end_dt)
    q = select(func.count()).where(and_(CurrentActivePlan.valid_to >= start_dt, CurrentActivePlan.valid_to <= end_dt))
    res = await db.execute(q)
    return int(res.scalar_one() or 0)

async def activation_trend_by_day(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    start_dt = make_naive(start_dt); end_dt = make_naive(end_dt)
    q = (
        select(func.date_trunc("day", CurrentActivePlan.valid_from).label("day"), func.count().label("cnt"))
        .where(CurrentActivePlan.valid_from >= start_dt, CurrentActivePlan.valid_from <= end_dt)
        .group_by("day").order_by("day")
    )
    res = await db.execute(q)
    rows = res.all()
    mapping = {r[0].date(): int(r[1]) for r in rows}
    out = []
    cur = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    last = end_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    from datetime import timedelta
    while cur.date() <= last.date():
        out.append({"date": cur.date().isoformat(), "count": mapping.get(cur.date(), 0)})
        cur += timedelta(days=1)
    return out

async def activation_trend_by_month(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    start_dt = make_naive(start_dt); end_dt = make_naive(end_dt)
    q = (
        select(func.date_trunc("month", CurrentActivePlan.valid_from).label("month"), func.count().label("cnt"))
        .where(CurrentActivePlan.valid_from >= start_dt, CurrentActivePlan.valid_from <= end_dt)
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

async def avg_plan_duration_days(db: AsyncSession) -> float:
    """
    Average(valid_to - valid_from) in days.
    Uses extract(epoch(...)) / 86400.
    """
    # SQL: avg(extract(epoch from valid_to - valid_from)) / 86400.0
    epoch_avg = func.avg(func.extract("epoch", CurrentActivePlan.valid_to - CurrentActivePlan.valid_from))
    q = select(func.coalesce(epoch_avg, 0))
    res = await db.execute(q)
    val = res.scalar_one()
    return float(val) / 86400.0 if val is not None else 0.0

async def upcoming_expirations(db: AsyncSession, start_dt: datetime, end_dt: datetime, limit: int = 50) -> List[Dict]:
    start_dt = make_naive(start_dt); end_dt = make_naive(end_dt)
    q = (
        select(CurrentActivePlan.id,
               CurrentActivePlan.user_id,
               CurrentActivePlan.plan_id,
               CurrentActivePlan.phone_number,
               CurrentActivePlan.valid_from,
               CurrentActivePlan.valid_to,
               CurrentActivePlan.status)
        .where(and_(CurrentActivePlan.valid_to >= start_dt, CurrentActivePlan.valid_to <= end_dt))
        .order_by(CurrentActivePlan.valid_to.asc())
        .limit(limit)
    )
    res = await db.execute(q)
    return [
        {
            "id": int(r[0]),
            "user_id": int(r[1]) if r[1] is not None else None,
            "plan_id": int(r[2]) if r[2] is not None else None,
            "phone_number": r[3],
            "valid_from": r[4],
            "valid_to": r[5],
            "status": r[6].value if hasattr(r[6], "value") else r[6],
        }
        for r in res.all()
    ]

async def top_users_by_active_plans(db: AsyncSession, limit: int = 10) -> List[Dict]:
    q = select(CurrentActivePlan.user_id, func.count()).group_by(CurrentActivePlan.user_id).order_by(func.count().desc()).limit(limit)
    res = await db.execute(q)
    return [{"user_id": r[0], "count": int(r[1])} for r in res.all()]

async def phone_number_duplicates(db: AsyncSession, min_count: int = 2) -> List[Dict]:
    q = select(CurrentActivePlan.phone_number, func.count()).group_by(CurrentActivePlan.phone_number).having(func.count() >= min_count).order_by(func.count().desc())
    res = await db.execute(q)
    return [{"phone_number": r[0], "count": int(r[1])} for r in res.all()]
