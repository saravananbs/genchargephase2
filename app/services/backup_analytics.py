from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from ..crud import backup_analytics as crud_backups
from ..schemas.backup_analytics import (
    BackupsReport, PeriodCount, PeriodSize, TrendPoint, TrendMonthPoint,
    DistributionItem, BackupItem
)

TZ = ZoneInfo("Asia/Kolkata")

def now_tz() -> datetime:
    return datetime.now(TZ)

def start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)

def end_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)

def month_delta(dt: datetime, months: int) -> datetime:
    # subtract months (months can be positive or negative)
    year = dt.year - (months // 12)
    month = dt.month - (months % 12)
    while month <= 0:
        month += 12
        year -= 1
    return datetime(year, month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, tzinfo=TZ)

def build_periods():
    now = now_tz()
    today_start = start_of_day(now)
    periods = {}
    periods["yesterday"] = (today_start - timedelta(days=1), end_of_day(today_start - timedelta(days=1)))
    periods["last_week"] = (today_start - timedelta(days=7), end_of_day(today_start - timedelta(days=1)))
    periods["last_30_days"] = (today_start - timedelta(days=30), end_of_day(today_start - timedelta(days=1)))
    periods["last_3_months"] = (today_start - timedelta(days=90), end_of_day(today_start - timedelta(days=1)))
    periods["last_6_months"] = (today_start - timedelta(days=183), end_of_day(today_start - timedelta(days=1)))
    periods["last_year"] = (today_start - timedelta(days=365), end_of_day(today_start - timedelta(days=1)))
    return periods

async def build_backups_report(db: AsyncSession) -> BackupsReport:
    gen_at = now_tz()

    tot = await crud_backups.total_backups(db)

    # period ranges
    periods = build_periods()
    period_counts = {}
    period_sizes = {}
    for k, (s, e) in periods.items():
        cnt = await crud_backups.count_between(db, s, e)
        sz = await crud_backups.sum_size_between(db, s, e)
        period_counts[k] = PeriodCount(period_label=k, count=cnt)
        period_sizes[k] = PeriodSize(period_label=k, total_size_mb=sz)

    # trends
    last7_s, last7_e = periods["last_week"]
    trend_7d = await crud_backups.trend_by_day(db, last7_s, last7_e)

    last30_s, last30_e = periods["last_30_days"]
    trend_30d = await crud_backups.trend_by_day(db, last30_s, last30_e)

    trend_6m = await crud_backups.trend_by_month(db, *periods["last_6_months"])
    trend_12m = await crud_backups.trend_by_month(db, *periods["last_year"])

    # distributions
    status_dist_raw = await crud_backups.distribution_by_status(db)
    data_dist_raw = await crud_backups.distribution_by_data_type(db)
    denom = tot or 1
    status_dist = [DistributionItem(key=r["key"], count=r["count"], percent=round(r["count"]/denom*100.0,2)) for r in status_dist_raw]
    data_dist = [DistributionItem(key=r["key"], count=r["count"], percent=round(r["count"]/denom*100.0,2)) for r in data_dist_raw]

    # growth rates: week_over_week and month_over_month
    prev7_s = last7_s - timedelta(days=7)
    prev7_e = last7_s - timedelta(days=1)
    last7_cnt = await crud_backups.count_between(db, last7_s, last7_e)
    prev7_cnt = await crud_backups.count_between(db, prev7_s, prev7_e)
    week_over_week_pct = ((last7_cnt - prev7_cnt) / prev7_cnt * 100.0) if prev7_cnt else (100.0 if last7_cnt else 0.0)

    prev30_s = last30_s - timedelta(days=30)
    prev30_e = last30_s - timedelta(days=1)
    last30_cnt = await crud_backups.count_between(db, last30_s, last30_e)
    prev30_cnt = await crud_backups.count_between(db, prev30_s, prev30_e)
    month_over_month_pct = ((last30_cnt - prev30_cnt) / prev30_cnt * 100.0) if prev30_cnt else (100.0 if last30_cnt else 0.0)

    # last backup and total storage + averages + top largest
    last_b = await crud_backups.last_backup_item(db)
    total_storage_mb = await crud_backups.total_storage(db)
    avg_size = await crud_backups.avg_size_between(db, datetime(1970,1,1,tzinfo=TZ), gen_at) if tot else 0.0
    top_largest = await crud_backups.top_largest_backups(db, limit=10)

    # recent failures (last week)
    recent_failures = await crud_backups.recent_failures(db, last7_s, last7_e, limit=20)

    # backups by creator
    by_creator = await crud_backups.backups_by_creator(db)

    report = BackupsReport(
        generated_at=gen_at,
        totals={
            "total_backups": tot
        },
        period_counts=period_counts,
        period_sizes=period_sizes,
        trends={
            "last_7_days": [TrendPoint(**p) for p in trend_7d],
            "last_30_days": [TrendPoint(**p) for p in trend_30d],
        },
        monthly_trends={
            "last_6_months": [TrendMonthPoint(month=m["month"], count=m["count"]) for m in trend_6m],
            "last_1_year": [TrendMonthPoint(month=m["month"], count=m["count"]) for m in trend_12m],
        },
        distributions={
            "status": status_dist,
            "backup_data": data_dist
        },
        growth_rates={
            "week_over_week_pct": round(week_over_week_pct, 2),
            "month_over_month_pct": round(month_over_month_pct, 2)
        },
        last_backup=BackupItem(**last_b) if last_b else None,
        total_storage_mb=total_storage_mb,
        avg_backup_size_mb=round(avg_size, 2),
        top_largest_backups=[BackupItem(**b) for b in top_largest],
        recent_failures=[BackupItem(**b) for b in recent_failures],
        backups_by_creator=by_creator
    )
    return report
