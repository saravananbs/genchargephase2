from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from ..crud.analytics import (
    crud_avg_wallet_balance, crud_count_users_between, crud_count_users_by_status,
    crud_count_users_by_type, crud_top_referrers, crud_total_users,
    crud_users_trend_by_day, crud_users_trend_by_month, total_admins, count_admins_between, 
    admins_by_role, admins_trend_by_month
)
from ..models.users import UserStatus
from ..utils.analytics import range_for_period, now_tz, period_ranges
from ..schemas.analytics import UsersReport, TrendPoint, DistributionItem, PeriodCount, AdminsReport

# Users service
async def build_users_report(db: AsyncSession) -> UsersReport:
    gen_at = now_tz()

    # totals
    total_users = await crud_total_users(db)
    status_counts = await crud_count_users_by_status(db)
    type_counts = await crud_count_users_by_type(db)
    avg_wallet = await crud_avg_wallet_balance(db)

    # period counts
    periods = {
        "yesterday": range_for_period("yesterday"),
        "last_week": range_for_period("last_week"),
        "last_30_days": range_for_period("last_30_days"),
        "last_6_months": range_for_period("last_6_months"),
        "last_year": range_for_period("last_year"),
    }
    period_counts = {}
    for label, (start_dt, end_dt) in periods.items():
        count = await crud_count_users_between(db, start_dt, end_dt)
        period_counts[label] = {"period_label": label, "count": count}

    # trends
    # last 7 days trend
    last7_start, last7_end = range_for_period("last_week")
    trend_7d = await crud_users_trend_by_day(db, last7_start, last7_end)

    # last 30 days daily trend
    last30_start, last30_end = range_for_period("last_30_days")
    trend_30d = await crud_users_trend_by_day(db, last30_start, last30_end)

    # last 6 months monthly trend
    last6_start, last6_end = range_for_period("last_6_months")
    trend_6m = await crud_users_trend_by_month(db, last6_start, last6_end)

    # last year monthly trend
    lasty_start, lasty_end = range_for_period("last_year")
    trend_12m = await crud_users_trend_by_month(db, lasty_start, lasty_end)

    # growth rates: week-over-week, month-over-month (simple percent change)
    # week-over-week: compare last 7 days vs previous 7 days
    prev7_start = last7_start - timedelta(days=7)
    prev7_end = last7_start - timedelta(days=1)
    last7_count = await crud_count_users_between(db, last7_start, last7_end)
    prev7_count = await crud_count_users_between(db, prev7_start, prev7_end)
    week_over_week_pct = ((last7_count - prev7_count) / prev7_count * 100.0) if prev7_count else (100.0 if last7_count else 0.0)

    # month-over-month: last 30 days vs previous 30 days
    prev30_start = last30_start - timedelta(days=30)
    prev30_end = last30_start - timedelta(days=1)
    last30_count = await crud_count_users_between(db, last30_start, last30_end)
    prev30_count = await crud_count_users_between(db, prev30_start, prev30_end)
    month_over_month_pct = ((last30_count - prev30_count) / prev30_count * 100.0) if prev30_count else (100.0 if last30_count else 0.0)

    # distributions
    total_for_dist = total_users or 1
    status_dist = [
        {
            "key": s["status"],
            "count": s["count"],
            "percent": round(s["count"] / total_for_dist * 100.0, 2)
        }
        for s in status_counts
    ]
    type_dist = [
        {
            "key": t["type"],
            "count": t["count"],
            "percent": round(t["count"] / total_for_dist * 100.0, 2)
        }
        for t in type_counts
    ]

    # top referrers
    top_referrers = await crud_top_referrers(db, limit=10)

    payload = UsersReport(
        generated_at=gen_at,
        totals={
            "total_users": total_users,
            "active_users": next((s["count"] for s in status_counts if s["status"] == UserStatus.active.value), 0),
            "blocked_users": next((s["count"] for s in status_counts if s["status"] == UserStatus.blocked.value), 0),
            "deactivated_users": next((s["count"] for s in status_counts if s["status"] == UserStatus.deactive.value), 0),
        },
        averages={
            "avg_wallet_balance": round(avg_wallet, 2),
        },
        period_counts={k: PeriodCount(**v) for k, v in period_counts.items()},
        trends={
            "last_7_days": [TrendPoint(**p) for p in trend_7d],
            "last_30_days": [TrendPoint(**p) for p in trend_30d],
            "last_6_months": [TrendPoint(date=m["month"], count=m["count"]) for m in trend_6m],
            "last_1_year": [TrendPoint(date=m["month"], count=m["count"]) for m in trend_12m],
        },
        distributions={
            "status": [DistributionItem(**d) for d in status_dist],
            "user_type": [DistributionItem(**d) for d in type_dist],
        },
        growth_rates={
            "week_over_week_pct": round(week_over_week_pct, 2),
            "month_over_month_pct": round(month_over_month_pct, 2),
        },
        top_referrers=top_referrers,
    )
    return payload


# Admin service
async def build_admins_report(db: AsyncSession) -> AdminsReport:
    gen_at = now_tz()
    totals = {}
    tot_admins = await total_admins(db)
    totals["total_admins"] = tot_admins

    periods = period_ranges()
    period_counts = {}
    for label, (start_dt, end_dt) in periods.items():
        cnt = await count_admins_between(db, start_dt, end_dt)
        period_counts[label] = PeriodCount(period_label=label, count=cnt)

    # trends monthly (6 months / 12 months)
    trend_6m = await admins_trend_by_month(db, *periods["last_6_months"])
    trend_12m = await admins_trend_by_month(db, *periods["last_year"])

    # role distribution
    roles = await admins_by_role(db)
    denom_admins = tot_admins or 1
    role_dist = [DistributionItem(key=str(r["role_id"]), count=r["count"], percent=round(r["count"] / denom_admins * 100.0, 2)) for r in roles]

    # growth rates - compare last 30 days vs previous 30
    last30_start, last30_end = periods["last_30_days"]
    prev30_start = last30_start - timedelta(days=30)
    prev30_end = last30_start - timedelta(days=1)
    last30_count = await count_admins_between(db, last30_start, last30_end)
    prev30_count = await count_admins_between(db, prev30_start, prev30_end)
    month_over_month_pct = ((last30_count - prev30_count) / prev30_count * 100.0) if prev30_count else (100.0 if last30_count else 0.0)

    report = AdminsReport(
        generated_at=gen_at,
        totals=totals,
        period_counts=period_counts,
        trends={
            "last_6_months": [TrendPoint(date=m["month"], count=m["count"]) for m in trend_6m],
            "last_1_year": [TrendPoint(date=m["month"], count=m["count"]) for m in trend_12m]
        },
        distributions={"roles": role_dist},
        growth_rates={"month_over_month_pct": round(month_over_month_pct, 2)}
    )
    return report