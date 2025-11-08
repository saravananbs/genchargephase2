from typing import List, Dict, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select, func, and_, cast, Numeric
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.backup import Backup


TZ = ZoneInfo("Asia/Kolkata")

async def total_backups(db: AsyncSession) -> int:
    q = select(func.count()).select_from(Backup)
    res = await db.execute(q)
    return int(res.scalar_one() or 0)

async def count_between(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> int:
    q = select(func.count()).select_from(Backup).where(
        and_(Backup.created_at >= start_dt, Backup.created_at <= end_dt)
    )
    res = await db.execute(q)
    return int(res.scalar_one() or 0)

async def sum_size_between(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> int:
    # cast size_mb (string) -> Numeric for sum; nulls will be ignored
    q = select(func.coalesce(func.sum(cast(Backup.size_mb, Numeric)), 0)).where(
        and_(Backup.created_at >= start_dt, Backup.created_at <= end_dt)
    )
    res = await db.execute(q)
    val = res.scalar_one()
    return int(val or 0)

async def avg_size_between(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> float:
    q = select(func.coalesce(func.avg(cast(Backup.size_mb, Numeric)), 0)).where(
        and_(Backup.created_at >= start_dt, Backup.created_at <= end_dt)
    )
    res = await db.execute(q)
    val = res.scalar_one()
    return float(val or 0.0)

async def distribution_by_status(db: AsyncSession) -> List[Dict]:
    q = select(Backup.backup_status, func.count()).group_by(Backup.backup_status)
    res = await db.execute(q)
    return [{"key": r[0], "count": int(r[1])} for r in res.all()]

async def distribution_by_data_type(db: AsyncSession) -> List[Dict]:
    q = select(Backup.backup_data, func.count()).group_by(Backup.backup_data)
    res = await db.execute(q)
    return [{"key": r[0], "count": int(r[1])} for r in res.all()]

async def trend_by_day(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    q = (
        select(func.date_trunc("day", Backup.created_at).label("day"), func.count().label("cnt"))
        .where(Backup.created_at >= start_dt, Backup.created_at <= end_dt)
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
        from datetime import timedelta
        cur = cur + timedelta(days=1)
    return out

async def trend_by_month(db: AsyncSession, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    q = (
        select(func.date_trunc("month", Backup.created_at).label("month"), func.count().label("cnt"))
        .where(Backup.created_at >= start_dt, Backup.created_at <= end_dt)
        .group_by("month").order_by("month")
    )
    res = await db.execute(q)
    rows = res.all()
    mapping = {r[0].date().replace(day=1): int(r[1]) for r in rows}
    out = []
    # build month iterator
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

async def last_backup_item(db: AsyncSession) -> Optional[Dict]:
    q = select(
        Backup.backup_id,
        Backup.snapshot_name,
        Backup.storage_url,
        Backup.backup_status,
        cast(Backup.size_mb, Numeric).label("size_mb"),
        Backup.created_at,
        Backup.created_by
    ).order_by(Backup.created_at.desc()).limit(1)
    res = await db.execute(q)
    row = res.first()
    if not row:
        return None
    return {
        "backup_id": row[0],
        "snapshot_name": row[1],
        "storage_url": row[2],
        "backup_status": row[3],
        "size_mb": int(row[4]) if row[4] is not None else None,
        "created_at": row[5],
        "created_by": row[6],
    }

async def total_storage(db: AsyncSession) -> int:
    q = select(func.coalesce(func.sum(cast(Backup.size_mb, Numeric)), 0))
    res = await db.execute(q)
    val = res.scalar_one()
    return int(val or 0)

async def top_largest_backups(db: AsyncSession, limit: int = 10) -> List[Dict]:
    q = select(
        Backup.backup_id,
        Backup.snapshot_name,
        Backup.storage_url,
        Backup.backup_status,
        cast(Backup.size_mb, Numeric).label("size_mb"),
        Backup.created_at,
        Backup.created_by
    ).order_by(cast(Backup.size_mb, Numeric).desc()).limit(limit)
    res = await db.execute(q)
    out = []
    for r in res.all():
        out.append({
            "backup_id": r[0],
            "snapshot_name": r[1],
            "storage_url": r[2],
            "backup_status": r[3],
            "size_mb": int(r[4]) if r[4] is not None else None,
            "created_at": r[5],
            "created_by": r[6],
        })
    return out

async def recent_failures(db: AsyncSession, start_dt: datetime, end_dt: datetime, limit: int = 20) -> List[Dict]:
    q = select(
        Backup.backup_id,
        Backup.snapshot_name,
        Backup.storage_url,
        Backup.backup_status,
        cast(Backup.size_mb, Numeric).label("size_mb"),
        Backup.created_at,
        Backup.created_by
    ).where(
        and_(
            Backup.created_at >= start_dt,
            Backup.created_at <= end_dt,
            Backup.backup_status.ilike("%fail%")
        )
    ).order_by(Backup.created_at.desc()).limit(limit)
    res = await db.execute(q)
    return [
        {
            "backup_id": r[0],
            "snapshot_name": r[1],
            "storage_url": r[2],
            "backup_status": r[3],
            "size_mb": int(r[4]) if r[4] is not None else None,
            "created_at": r[5],
            "created_by": r[6],
        }
        for r in res.all()
    ]

async def backups_by_creator(db: AsyncSession) -> List[Dict]:
    q = select(Backup.created_by, func.count()).group_by(Backup.created_by).order_by(func.count().desc())
    res = await db.execute(q)
    return [{"created_by": r[0], "count": int(r[1])} for r in res.all()]
