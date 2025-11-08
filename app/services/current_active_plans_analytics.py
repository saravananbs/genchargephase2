from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from ..crud import current_active_plan_analytics as crud
from ..schemas.current_active_plans_analytics import (
    CurrentActivePlansReport, PeriodCount, TrendPoint, TrendMonthPoint,
    DistributionItem, ActivePlanItem, TopUserItem
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

async def build_current_active_plans_report(db: AsyncSession) -> CurrentActivePlansReport:
    gen_at = now_tz()

    totals = {}
    total = await crud.total_active_plans(db)
    totals["total_active_plans"] = total

    status_counts = await crud.count_by_status(db)
    plan_counts = await crud.count_by_plan(db)

    periods = build_periods()
    period_activations = {}
    period_expirations = {}
    for label, (s, e) in periods.items():
        activations = await crud.count_activations_between(db, s, e)
        expirations = await crud.count_expirations_between(db, s, e)
        period_activations[label] = PeriodCount(period_label=label, count=activations)
        period_expirations[label] = PeriodCount(period_label=label, count=expirations)

    # trends
    last7_s, last7_e = periods["last_week"]
    trend_7d = await crud.activation_trend_by_day(db, last7_s, last7_e)

    last30_s, last30_e = periods["last_30_days"]
    trend_30d = await crud.activation_trend_by_day(db, last30_s, last30_e)

    trend_6m = await crud.activation_trend_by_month(db, *periods["last_6_months"])
    trend_12m = await crud.activation_trend_by_month(db, *periods["last_year"])

    # growth rates: compare last7 vs previous7, last30 vs prev30
    prev7_s = last7_s - timedelta(days=7)
    prev7_e = last7_s - timedelta(days=1)
    last7_cnt = await crud.count_activations_between(db, last7_s, last7_e)
    prev7_cnt = await crud.count_activations_between(db, prev7_s, prev7_e)
    week_over_week_pct = ((last7_cnt - prev7_cnt) / prev7_cnt * 100.0) if prev7_cnt else (100.0 if last7_cnt else 0.0)

    prev30_s = last30_s - timedelta(days=30)
    prev30_e = last30_s - timedelta(days=1)
    last30_cnt = await crud.count_activations_between(db, last30_s, last30_e)
    prev30_cnt = await crud.count_activations_between(db, prev30_s, prev30_e)
    month_over_month_pct = ((last30_cnt - prev30_cnt) / prev30_cnt * 100.0) if prev30_cnt else (100.0 if last30_cnt else 0.0)

    # distributions: by status and by plan (percent)
    denom = total or 1
    status_dist = [DistributionItem(key=s["status"], count=s["count"], percent=round(s["count"]/denom*100.0, 2)) for s in status_counts]
    plan_dist = [DistributionItem(key=str(p["plan_id"]), count=p["count"], percent=round(p["count"]/denom*100.0, 2)) for p in plan_counts]

    # avg duration
    avg_duration_days = await crud.avg_plan_duration_days(db)

    # upcoming expirations (next 7 days)
    upcoming_start = now_tz()
    upcoming_end = now_tz() + timedelta(days=7)
    upcoming = await crud.upcoming_expirations(db, upcoming_start, upcoming_end, limit=50)
    upcoming_items = [ActivePlanItem(**u) for u in upcoming]

    # top users
    top_users_raw = await crud.top_users_by_active_plans(db, limit=10)
    top_users = [TopUserItem(user_id=r["user_id"], active_plan_count=r["count"]) for r in top_users_raw]

    # phone duplicates
    duplicates = await crud.phone_number_duplicates(db, min_count=2)

    report = CurrentActivePlansReport(
        generated_at=gen_at,
        totals=totals,
        period_activations=period_activations,
        period_expirations=period_expirations,
        trends={
            "last_7_days": [TrendPoint(**p) for p in trend_7d],
            "last_30_days": [TrendPoint(**p) for p in trend_30d]
        },
        monthly_trends={
            "last_6_months": [TrendMonthPoint(month=m["month"], count=m["count"]) for m in trend_6m],
            "last_1_year": [TrendMonthPoint(month=m["month"], count=m["count"]) for m in trend_12m],
        },
        distributions={
            "by_status": status_dist,
            "by_plan": plan_dist
        },
        growth_rates={
            "week_over_week_pct": round(week_over_week_pct, 2),
            "month_over_month_pct": round(month_over_month_pct, 2)
        },
        avg_plan_duration_days=round(avg_duration_days, 2),
        upcoming_expirations=upcoming_items,
        top_users=top_users,
        phone_number_duplicates=duplicates
    )
    return report
