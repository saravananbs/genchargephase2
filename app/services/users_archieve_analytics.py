from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.ext.asyncio import AsyncSession

from ..crud import users_archieve_analytics as crud_users_archive
from ..schemas.users_archive_analytics import (
    UsersArchiveReport, PeriodCount, TrendPoint, TrendMonthPoint, DistributionItem, ArchivedUserItem
)

TZ = ZoneInfo("Asia/Kolkata")

def now_tz() -> datetime:
    return datetime.now(TZ)

def start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)

def end_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)

def build_periods():
    now = now_tz()
    today_start = start_of_day(now)
    return {
        "yesterday": (today_start - timedelta(days=1), end_of_day(today_start - timedelta(days=1))),
        "last_week": (today_start - timedelta(days=7), end_of_day(today_start - timedelta(days=1))),
        "last_30_days": (today_start - timedelta(days=30), end_of_day(today_start - timedelta(days=1))),
        "last_3_months": (today_start - timedelta(days=90), end_of_day(today_start - timedelta(days=1))),
        "last_6_months": (today_start - timedelta(days=183), end_of_day(today_start - timedelta(days=1))),
        "last_year": (today_start - timedelta(days=365), end_of_day(today_start - timedelta(days=1))),
    }

async def build_users_archive_report(db: AsyncSession) -> UsersArchiveReport:
    gen_at = now_tz()

    # totals
    total_archived = await crud_users_archive.total_archived_users(db)
    type_raw = await crud_users_archive.distribution_by_user_type(db)
    status_raw = await crud_users_archive.distribution_by_status(db)

    totals = {
        "total_archived_users": total_archived,
        "prepaid_archived": next((r["count"] for r in type_raw if r["key"] == "prepaid"), 0),
        "postpaid_archived": next((r["count"] for r in type_raw if r["key"] == "postpaid"), 0),
        "active_archived": next((r["count"] for r in status_raw if r["key"] == "active"), 0),
        "blocked_archived": next((r["count"] for r in status_raw if r["key"] == "blocked"), 0),
    }

    # periods
    periods = build_periods()
    period_deletions = {}
    for label, (s, e) in periods.items():
        cnt = await crud_users_archive.count_deleted_between(db, s, e)
        period_deletions[label] = PeriodCount(period_label=label, count=cnt)

    # trends
    last7_s, last7_e = periods["last_week"]
    trend_7d = await crud_users_archive.deletion_trend_by_day(db, last7_s, last7_e)
    last30_s, last30_e = periods["last_30_days"]
    trend_30d = await crud_users_archive.deletion_trend_by_day(db, last30_s, last30_e)

    trend_6m = await crud_users_archive.deletion_trend_by_month(db, *periods["last_6_months"])
    trend_12m = await crud_users_archive.deletion_trend_by_month(db, *periods["last_year"])

    # averages & totals for wallet
    total_wallet = await crud_users_archive.total_wallet_in_archive(db)
    avg_wallet = await crud_users_archive.avg_wallet_balance(db)

    # growth rates (week-over-week & month-over-month) for deletions
    prev7_s = last7_s - timedelta(days=7); prev7_e = last7_s - timedelta(days=1)
    last7_cnt = await crud_users_archive.count_deleted_between(db, last7_s, last7_e)
    prev7_cnt = await crud_users_archive.count_deleted_between(db, prev7_s, prev7_e)
    week_over_week_pct = ((last7_cnt - prev7_cnt) / prev7_cnt * 100.0) if prev7_cnt else (100.0 if last7_cnt else 0.0)

    prev30_s = last30_s - timedelta(days=30); prev30_e = last30_s - timedelta(days=1)
    last30_cnt = await crud_users_archive.count_deleted_between(db, last30_s, last30_e)
    prev30_cnt = await crud_users_archive.count_deleted_between(db, prev30_s, prev30_e)
    month_over_month_pct = ((last30_cnt - prev30_cnt) / prev30_cnt * 100.0) if prev30_cnt else (100.0 if last30_cnt else 0.0)

    # top by wallet & recent deletions
    top_wallet_raw = await crud_users_archive.top_by_wallet(db, limit=10)
    top_wallet_items = [ArchivedUserItem(**u) for u in top_wallet_raw]
    recent_raw = await crud_users_archive.recent_deleted(db, limit=20)
    recent_items = [ArchivedUserItem(**u) for u in recent_raw]

    # phone duplicates
    duplicates = await crud_users_archive.phone_number_duplicates(db)

    # distributions formatted
    denom = total_archived or 1
    type_dist = [DistributionItem(key=r["key"], count=r["count"], percent=round(r["count"]/denom*100.0, 2)) for r in type_raw]
    status_dist = [DistributionItem(key=r["key"], count=r["count"], percent=round(r["count"]/denom*100.0, 2)) for r in status_raw]

    report = UsersArchiveReport(
        generated_at=gen_at,
        totals=totals,
        period_deletions=period_deletions,
        trends={
            "last_7_days": [TrendPoint(**p) for p in trend_7d],
            "last_30_days": [TrendPoint(**p) for p in trend_30d]
        },
        monthly_trends={
            "last_6_months": [TrendMonthPoint(month=m["month"], count=m["count"]) for m in trend_6m],
            "last_1_year": [TrendMonthPoint(month=m["month"], count=m["count"]) for m in trend_12m]
        },
        distributions={
            "by_user_type": type_dist,
            "by_status": status_dist
        },
        averages={
            "avg_wallet_balance": round(avg_wallet, 2),
            "total_wallet_balance": round(total_wallet, 2)
        },
        growth_rates={
            "week_over_week_pct": round(week_over_week_pct, 2),
            "month_over_month_pct": round(month_over_month_pct, 2)
        },
        top_by_wallet=top_wallet_items,
        recent_deleted=recent_items,
        phone_number_duplicates=duplicates
    )
    return report
