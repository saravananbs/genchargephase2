# crud_plans.py
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.plans import Plan
from ..models.plan_groups import PlanGroup
from ..models.current_active_plans import CurrentActivePlan

TZ = ZoneInfo("Asia/Kolkata")

def make_naive(dt: Optional[datetime]) -> Optional[datetime]:
    """If dt is tz-aware, convert to UTC then drop tzinfo (for TIMESTAMP WITHOUT TIME ZONE)."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    return dt

# Total counts
async def total_plans(db: AsyncSession) -> int:
    q = select(func.count()).select_from(Plan)
    res = await db.execute(q)
    return int(res.scalar_one() or 0)

async def count_plans_between(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> int:
    start_dt = make_naive(start_dt); end_dt = make_naive(end_dt)
    q = select(func.count()).where(and_(Plan.created_at >= start_dt, Plan.created_at <= end_dt))
    res = await db.execute(q)
    return int(res.scalar_one() or 0)

# Activation / expiration counts from CurrentActivePlan
async def count_activations_between(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> int:
    start_dt = make_naive(start_dt); end_dt = make_naive(end_dt)
    q = select(func.count()).select_from(CurrentActivePlan).where(
        and_(CurrentActivePlan.valid_from >= start_dt, CurrentActivePlan.valid_from <= end_dt)
    )
    res = await db.execute(q)
    return int(res.scalar_one() or 0)

async def count_expirations_between(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> int:
    start_dt = make_naive(start_dt); end_dt = make_naive(end_dt)
    q = select(func.count()).select_from(CurrentActivePlan).where(
        and_(CurrentActivePlan.valid_to >= start_dt, CurrentActivePlan.valid_to <= end_dt)
    )
    res = await db.execute(q)
    return int(res.scalar_one() or 0)

# trends by day/month
async def trend_plans_by_day(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    start_dt = make_naive(start_dt); end_dt = make_naive(end_dt)
    q = (
        select(func.date_trunc("day", Plan.created_at).label("day"), func.count().label("cnt"))
        .where(Plan.created_at >= start_dt, Plan.created_at <= end_dt)
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

async def trend_plans_by_month(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    start_dt = make_naive(start_dt); end_dt = make_naive(end_dt)
    q = (
        select(func.date_trunc("month", Plan.created_at).label("month"), func.count().label("cnt"))
        .where(Plan.created_at >= start_dt, Plan.created_at <= end_dt)
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

# distributions
async def distribution_by_plan_type(db: AsyncSession) -> List[Dict]:
    q = select(Plan.plan_type, func.count()).group_by(Plan.plan_type)
    res = await db.execute(q)
    return [{"key": (r[0].value if hasattr(r[0], "value") else r[0]), "count": int(r[1])} for r in res.all()]

async def distribution_by_status(db: AsyncSession) -> List[Dict]:
    q = select(Plan.status, func.count()).group_by(Plan.status)
    res = await db.execute(q)
    return [{"key": (r[0].value if hasattr(r[0], "value") else r[0]), "count": int(r[1])} for r in res.all()]

async def distribution_by_group(db: AsyncSession) -> List[Dict]:
    q = select(Plan.group_id, func.count()).group_by(Plan.group_id).order_by(func.count().desc())
    res = await db.execute(q)
    return [{"key": (int(r[0]) if r[0] is not None else None), "count": int(r[1])} for r in res.all()]

# averages
async def avg_price(db: AsyncSession) -> float:
    q = select(func.coalesce(func.avg(Plan.price), 0))
    res = await db.execute(q)
    val = res.scalar_one()
    return float(val or 0.0)

async def avg_validity(db: AsyncSession) -> float:
    q = select(func.coalesce(func.avg(Plan.validity), 0))
    res = await db.execute(q)
    val = res.scalar_one()
    return float(val or 0.0)

# Most popular plans
async def most_popular_plans(db: AsyncSession, limit: int = 10) -> List[Dict]:
    q = (
        select(
            Plan.plan_id,
            Plan.plan_name,
            Plan.plan_type,
            Plan.group_id,
            Plan.validity,
            Plan.price,
            Plan.most_popular,
            Plan.status,
            Plan.created_at,
            Plan.created_by
        )
        .where(Plan.most_popular == True)
        .order_by(Plan.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(q)
    return [
        {
            "plan_id": int(r[0]),
            "plan_name": r[1],
            "plan_type": (r[2].value if hasattr(r[2], "value") else r[2]),
            "group_id": int(r[3]) if r[3] is not None else None,
            "validity": int(r[4]) if r[4] is not None else None,
            "price": int(r[5]) if r[5] is not None else 0,
            "most_popular": bool(r[6]),
            "status": (r[7].value if hasattr(r[7], "value") else r[7]),
            "created_at": r[8],
            "created_by": int(r[9]) if r[9] is not None else None
        }
        for r in res.all()
    ]

# Top plans by current active count (join CurrentActivePlan)
async def top_plans_by_active_count(db: AsyncSession, limit: int = 10) -> List[Dict]:
    # join Plans -> CurrentActivePlans on plan_id
    plan_tbl = Plan.__table__.alias("p")
    active_tbl = CurrentActivePlan.__table__.alias("a")
    q = (
        select(plan_tbl.c.plan_id, plan_tbl.c.plan_name, func.count(active_tbl.c.id).label("active_count"))
        .select_from(plan_tbl.join(active_tbl, plan_tbl.c.plan_id == active_tbl.c.plan_id))
        .group_by(plan_tbl.c.plan_id, plan_tbl.c.plan_name)
        .order_by(func.count(active_tbl.c.id).desc())
        .limit(limit)
    )
    res = await db.execute(q)
    return [{"plan_id": int(r[0]), "plan_name": r[1], "active_count": int(r[2])} for r in res.all()]

# plans by creator
async def plans_by_creator(db: AsyncSession) -> List[Dict]:
    q = select(Plan.created_by, func.count()).group_by(Plan.created_by).order_by(func.count().desc())
    res = await db.execute(q)
    return [{"created_by": r[0], "count": int(r[1])} for r in res.all()]
