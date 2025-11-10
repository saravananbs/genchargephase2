from typing import List, Dict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.transactions import Transaction

TZ = ZoneInfo("Asia/Kolkata")

def make_naive(dt: datetime):
    """
    Convert a timezone-aware datetime to a UTC-naive datetime suitable for
    TIMESTAMP WITHOUT TIME ZONE queries.

    Args:
        dt (datetime): A possibly timezone-aware datetime.

    Returns:
        datetime: A naive datetime in UTC if input was aware, otherwise the
        original datetime.
    """
    if dt.tzinfo is not None:
        return dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    return dt

# ---------- TOTALS ----------
async def total_transactions(db: AsyncSession) -> int:
    """
    Count total number of transactions in the database.

    Args:
        db (AsyncSession): Async database session.

    Returns:
        int: Total transaction count (0 if none).
    """
    q = select(func.count()).select_from(Transaction)
    res = await db.execute(q)
    return int(res.scalar_one() or 0)

async def total_amount(db: AsyncSession) -> float:
    """
    Sum the amount of all transactions.

    Args:
        db (AsyncSession): Async database session.

    Returns:
        float: Sum of transaction amounts (0.0 if none).
    """
    q = select(func.coalesce(func.sum(Transaction.amount), 0))
    res = await db.execute(q)
    return float(res.scalar_one() or 0.0)

async def totals_by_type(db: AsyncSession) -> Dict[str, float]:
    """
    Aggregate transaction counts and amounts grouped by transaction type.

    Args:
        db (AsyncSession): Async database session.

    Returns:
        Dict[str, Dict]: Mapping of txn_type -> {"count": int, "amount": float}.
    """
    q = select(Transaction.txn_type, func.count(), func.sum(Transaction.amount)).group_by(Transaction.txn_type)
    res = await db.execute(q)
    return {r[0].value: {"count": int(r[1]), "amount": float(r[2] or 0.0)} for r in res.all()}

async def totals_by_status(db: AsyncSession) -> Dict[str, int]:
    """
    Aggregate transaction counts grouped by status.

    Args:
        db (AsyncSession): Async database session.

    Returns:
        Dict[str, int]: Mapping of status -> count.
    """
    q = select(Transaction.status, func.count()).group_by(Transaction.status)
    res = await db.execute(q)
    return {r[0].value: int(r[1]) for r in res.all()}

# ---------- PERIOD QUERIES ----------
async def count_and_amount_between(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> Dict:
    """
    Count transactions and sum amounts between two datetimes (inclusive).

    Args:
        db (AsyncSession): Async database session.
        start_dt (datetime): Start datetime (inclusive).
        end_dt (datetime): End datetime (inclusive).

    Returns:
        Dict: {"count": int, "total_amount": float}
    """
    start_dt, end_dt = make_naive(start_dt), make_naive(end_dt)
    q = select(func.count(), func.coalesce(func.sum(Transaction.amount), 0)).where(
        and_(Transaction.created_at >= start_dt, Transaction.created_at <= end_dt)
    )
    res = await db.execute(q)
    row = res.first()
    return {"count": int(row[0] or 0), "total_amount": float(row[1] or 0)}

# ---------- TRENDS ----------
async def trend_by_day(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    """
    Produce a day-by-day trend of transaction counts and amounts between two dates.

    Args:
        db (AsyncSession): Async database session.
        start_dt (datetime): Start datetime (inclusive).
        end_dt (datetime): End datetime (inclusive).

    Returns:
        List[Dict]: List of daily points: {"date": ISO-date, "count": int, "total_amount": float}.
    """
    start_dt, end_dt = make_naive(start_dt), make_naive(end_dt)
    q = (
        select(
            func.date_trunc("day", Transaction.created_at).label("day"),
            func.count().label("cnt"),
            func.coalesce(func.sum(Transaction.amount), 0).label("amt"),
        )
        .where(Transaction.created_at >= start_dt, Transaction.created_at <= end_dt)
        .group_by("day")
        .order_by("day")
    )
    res = await db.execute(q)
    rows = res.all()
    mapping = {r[0].date(): {"count": int(r[1]), "amt": float(r[2])} for r in rows}
    out = []
    cur = start_dt
    while cur.date() <= end_dt.date():
        m = mapping.get(cur.date(), {"count": 0, "amt": 0})
        out.append({"date": cur.date().isoformat(), "count": m["count"], "total_amount": m["amt"]})
        cur += timedelta(days=1)
    return out

async def trend_by_month(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    """
    Produce a month-by-month trend of transaction counts and amounts between two dates.

    Args:
        db (AsyncSession): Async database session.
        start_dt (datetime): Start datetime (inclusive).
        end_dt (datetime): End datetime (inclusive).

    Returns:
        List[Dict]: List of monthly points: {"month": ISO-month, "count": int, "total_amount": float}.
    """
    start_dt, end_dt = make_naive(start_dt), make_naive(end_dt)
    q = (
        select(
            func.date_trunc("month", Transaction.created_at).label("month"),
            func.count().label("cnt"),
            func.coalesce(func.sum(Transaction.amount), 0).label("amt"),
        )
        .where(Transaction.created_at >= start_dt, Transaction.created_at <= end_dt)
        .group_by("month")
        .order_by("month")
    )
    res = await db.execute(q)
    return [{"month": r[0].date().isoformat(), "count": int(r[1]), "total_amount": float(r[2])} for r in res.all()]

# ---------- DISTRIBUTIONS ----------
async def distribution_by(field, db: AsyncSession) -> List[Dict]:
    """
    Compute a distribution (counts) grouped by the provided field.

    Args:
        field: ORM column or enum attribute to group by.
        db (AsyncSession): Async database session.

    Returns:
        List[Dict]: List of {"key": value, "count": int} entries.
    """
    q = select(field, func.count()).group_by(field)
    res = await db.execute(q)
    return [{"key": (r[0].value if hasattr(r[0], "value") else r[0]), "count": int(r[1])} for r in res.all()]

# ---------- TOP USERS ----------
async def top_users(db: AsyncSession, limit: int = 10) -> List[Dict]:
    """
    Return top users ordered by transaction amount.

    Args:
        db (AsyncSession): Async database session.
        limit (int): Maximum number of users to return.

    Returns:
        List[Dict]: List of {"user_id": int, "total_txns": int, "total_amount": float}.
    """
    q = (
        select(
            Transaction.user_id,
            func.count().label("cnt"),
            func.sum(Transaction.amount).label("total")
        )
        .group_by(Transaction.user_id)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(limit)
    )
    res = await db.execute(q)
    return [{"user_id": r[0], "total_txns": int(r[1]), "total_amount": float(r[2])} for r in res.all()]

# ---------- AVERAGES ----------
async def avg_amount(db: AsyncSession) -> float:
    """
    Compute the average transaction amount.

    Args:
        db (AsyncSession): Async database session.

    Returns:
        float: Average amount (0.0 if no transactions).
    """
    q = select(func.coalesce(func.avg(Transaction.amount), 0))
    res = await db.execute(q)
    return float(res.scalar_one() or 0.0)
