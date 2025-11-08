# crud_offers.py
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select, func, and_, cast
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.offers import Offer
from ..models.offer_types import OfferType

TZ = ZoneInfo("Asia/Kolkata")

def make_naive(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert aware datetime -> UTC naive for TIMESTAMP WITHOUT TIME ZONE columns."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    return dt

async def total_offers(db: AsyncSession) -> int:
    q = select(func.count()).select_from(Offer)
    res = await db.execute(q)
    return int(res.scalar_one() or 0)

async def count_between(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> int:
    start_dt = make_naive(start_dt)
    end_dt = make_naive(end_dt)
    q = select(func.count()).where(and_(Offer.created_at >= start_dt, Offer.created_at <= end_dt))
    res = await db.execute(q)
    return int(res.scalar_one() or 0)

async def count_special_between(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> int:
    start_dt = make_naive(start_dt)
    end_dt = make_naive(end_dt)
    q = select(func.count()).where(and_(Offer.created_at >= start_dt, Offer.created_at <= end_dt, Offer.is_special == True))
    res = await db.execute(q)
    return int(res.scalar_one() or 0)

async def distribution_by_status(db: AsyncSession) -> List[Dict]:
    q = select(Offer.status, func.count()).group_by(Offer.status)
    res = await db.execute(q)
    return [{"key": (r[0].value if hasattr(r[0], "value") else r[0]), "count": int(r[1])} for r in res.all()]

async def distribution_by_offer_type(db: AsyncSession) -> List[Dict]:
    # join to OfferType to get names if available
    q = (
        select(Offer.offer_type_id, func.count())
        .group_by(Offer.offer_type_id)
        .order_by(func.count().desc())
    )
    res = await db.execute(q)
    return [{"key": (str(r[0]) if r[0] is not None else "unknown"), "count": int(r[1])} for r in res.all()]

async def trend_by_day(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    start_dt = make_naive(start_dt); end_dt = make_naive(end_dt)
    q = (
        select(func.date_trunc("day", Offer.created_at).label("day"), func.count().label("cnt"))
        .where(Offer.created_at >= start_dt, Offer.created_at <= end_dt)
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

async def trend_by_month(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    start_dt = make_naive(start_dt); end_dt = make_naive(end_dt)
    q = (
        select(func.date_trunc("month", Offer.created_at).label("month"), func.count().label("cnt"))
        .where(Offer.created_at >= start_dt, Offer.created_at <= end_dt)
        .group_by("month").order_by("month")
    )
    res = await db.execute(q)
    rows = res.all()
    mapping = {r[0].date().replace(day=1): int(r[1]) for r in rows}
    out = []
    cur = datetime(start_dt.year, start_dt.month, 1, tzinfo=TZ)
    end_month = datetime(end_dt.year, end_dt.month, 1, tzinfo=TZ)
    def next_month(d):
        y = d.year + (d.month // 12)
        m = d.month % 12 + 1
        return datetime(y, m, 1, tzinfo=TZ)
    while cur.date() <= end_month.date():
        key = cur.date().replace(day=1)
        out.append({"month": key.isoformat(), "count": mapping.get(key, 0)})
        cur = next_month(cur)
    return out

async def avg_validity(db: AsyncSession) -> float:
    # average of Offer.offer_validity (nullable)
    q = select(func.coalesce(func.avg(Offer.offer_validity), 0))
    res = await db.execute(q)
    val = res.scalar_one()
    return float(val or 0.0)

async def top_recent_specials(db: AsyncSession, limit: int = 10) -> List[Dict]:
    q = (
        select(
            Offer.offer_id,
            Offer.offer_name,
            Offer.offer_type_id,
            Offer.is_special,
            Offer.offer_validity,
            Offer.created_at,
            Offer.created_by,
            Offer.status
        )
        .where(Offer.is_special == True)
        .order_by(Offer.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(q)
    return [
        {
            "offer_id": int(r[0]),
            "offer_name": r[1],
            "offer_type_id": int(r[2]) if r[2] is not None else None,
            "is_special": bool(r[3]),
            "offer_validity": int(r[4]) if r[4] is not None else None,
            "created_at": r[5],
            "created_by": int(r[6]) if r[6] is not None else None,
            "status": (r[7].value if hasattr(r[7], "value") else r[7])
        }
        for r in res.all()
    ]

async def offers_by_creator(db: AsyncSession) -> List[Dict]:
    q = select(Offer.created_by, func.count()).group_by(Offer.created_by).order_by(func.count().desc())
    res = await db.execute(q)
    return [{"created_by": r[0], "count": int(r[1])} for r in res.all()]

async def offers_by_type_detailed(db: AsyncSession) -> List[Dict]:
    # tries to get type name if OfferType model available; otherwise returns id
    # If OfferType is available, user should replace this query with a join.
    q = select(Offer.offer_type_id, func.count()).group_by(Offer.offer_type_id).order_by(func.count().desc())
    res = await db.execute(q)
    return [{"offer_type_id": r[0], "count": int(r[1])} for r in res.all()]
