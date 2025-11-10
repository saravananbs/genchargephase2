from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from ..crud import plan_analytics as crud_plans
from ..schemas.plan_analytics import (
    PlansReport, PeriodCount, TrendPoint, TrendMonthPoint, DistributionItem, PlanItem, TopPlanActiveCount
)

TZ = ZoneInfo("Asia/Kolkata")

def now_tz() -> datetime:
    """
    Return the current datetime localized to the service timezone.

    Returns:
        datetime: Timezone-aware datetime in `Asia/Kolkata`.
    """
    return datetime.now(TZ)

def start_of_day(dt: datetime) -> datetime:
    """
    Compute the start of the day (00:00:00) for a given datetime.

    Args:
        dt (datetime): A timezone-aware or naive datetime.

    Returns:
        datetime: Datetime set to the start of the same day.
    """
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)

def end_of_day(dt: datetime) -> datetime:
    """
    Compute the end of the day (23:59:59.999999) for a given datetime.

    Args:
        dt (datetime): A timezone-aware or naive datetime.

    Returns:
        datetime: Datetime set to the end of the same day.
    """
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)

def build_periods():
    """
    Build a mapping of common period labels to (start, end) datetimes.

    The returned datetimes are timezone-aware in the service timezone and
    typically exclude the current day (end at the end of the previous day).

    Returns:
        dict: Mapping from period name to a (start_datetime, end_datetime) tuple.
    """
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

async def build_plans_report(db: AsyncSession) -> PlansReport:
    """
    Build a plans analytics report aggregating totals, counts, trends, distributions and top items.

    This collects period-based counts for plan creation, activation and expiration,
    calculates trends by day/month, computes growth rates (week/month over week/month),
    and identifies most popular plans and top creators.

    Args:
        db (AsyncSession): Database session used to fetch metrics.

    Returns:
        PlansReport: Pydantic data structure containing comprehensive analytics for plans.

    Raises:
        Any exceptions raised by the underlying CRUD helpers (propagated).
    """
    gen_at = now_tz()

    total = await crud_plans.total_plans(db)
    totals = {"total_plans": total}

    # status breakdown for totals
    status_raw = await crud_plans.distribution_by_status(db)
    totals["active_plans_count"] = next((s["count"] for s in status_raw if s["key"] == "active"), 0)
    totals["inactive_plans_count"] = next((s["count"] for s in status_raw if s["key"] == "inactive"), 0)

    # averages
    avg_price = await crud_plans.avg_price(db)
    avg_validity = await crud_plans.avg_validity(db)

    # per-period counts
    periods = build_periods()
    period_counts = {}
    activation_counts = {}
    expiration_counts = {}
    for label, (s, e) in periods.items():
        period_counts[label] = PeriodCount(period_label=label, count=await crud_plans.count_plans_between(db, s, e))
        activation_counts[label] = PeriodCount(period_label=label, count=await crud_plans.count_activations_between(db, s, e))
        expiration_counts[label] = PeriodCount(period_label=label, count=await crud_plans.count_expirations_between(db, s, e))

    # trends
    last7_s, last7_e = periods["last_week"]
    trend_7d = await crud_plans.trend_plans_by_day(db, last7_s, last7_e)
    last30_s, last30_e = periods["last_30_days"]
    trend_30d = await crud_plans.trend_plans_by_day(db, last30_s, last30_e)
    trend_6m = await crud_plans.trend_plans_by_month(db, *periods["last_6_months"])
    trend_12m = await crud_plans.trend_plans_by_month(db, *periods["last_year"])

    # distributions
    plan_type_raw = await crud_plans.distribution_by_plan_type(db)
    group_raw = await crud_plans.distribution_by_group(db)
    denom = total or 1
    plan_type_dist = [DistributionItem(key=r["key"], count=r["count"], percent=round(r["count"]/denom*100.0, 2)) for r in plan_type_raw]
    group_dist = [DistributionItem(key=str(r["key"]), count=r["count"], percent=round(r["count"]/denom*100.0, 2)) for r in group_raw]

    # growth rates: week-over-week (new plans) & month-over-month
    prev7_s = last7_s - timedelta(days=7); prev7_e = last7_s - timedelta(days=1)
    last7_cnt = await crud_plans.count_plans_between(db, last7_s, last7_e)
    prev7_cnt = await crud_plans.count_plans_between(db, prev7_s, prev7_e)
    week_over_week_pct = ((last7_cnt - prev7_cnt) / prev7_cnt * 100.0) if prev7_cnt else (100.0 if last7_cnt else 0.0)

    prev30_s = last30_s - timedelta(days=30); prev30_e = last30_s - timedelta(days=1)
    last30_cnt = await crud_plans.count_plans_between(db, last30_s, last30_e)
    prev30_cnt = await crud_plans.count_plans_between(db, prev30_s, prev30_e)
    month_over_month_pct = ((last30_cnt - prev30_cnt) / prev30_cnt * 100.0) if prev30_cnt else (100.0 if last30_cnt else 0.0)

    # most popular & top by active
    most_popular_raw = await crud_plans.most_popular_plans(db, limit=10)
    most_popular_items = [PlanItem(**p) for p in most_popular_raw]
    top_by_active_raw = await crud_plans.top_plans_by_active_count(db, limit=10)
    top_by_active = [TopPlanActiveCount(plan_id=r["plan_id"], plan_name=r["plan_name"], active_count=r["active_count"]) for r in top_by_active_raw]

    # plans by creator
    by_creator = await crud_plans.plans_by_creator(db)

    report = PlansReport(
        generated_at=gen_at,
        totals=totals,
        period_counts=period_counts,
        activation_counts=activation_counts,
        expiration_counts=expiration_counts,
        trends={
            "last_7_days": [TrendPoint(**p) for p in trend_7d],
            "last_30_days": [TrendPoint(**p) for p in trend_30d]
        },
        monthly_trends={
            "last_6_months": [TrendMonthPoint(month=m["month"], count=m["count"]) for m in trend_6m],
            "last_1_year": [TrendMonthPoint(month=m["month"], count=m["count"]) for m in trend_12m]
        },
        distributions={
            "by_plan_type": plan_type_dist,
            "by_group": group_dist
        },
        averages={
            "avg_price": round(avg_price, 2),
            "avg_validity": round(avg_validity, 2)
        },
        growth_rates={
            "week_over_week_pct": round(week_over_week_pct, 2),
            "month_over_month_pct": round(month_over_month_pct, 2)
        },
        most_popular_plans=most_popular_items,
        top_plans_by_active_count=top_by_active,
        plans_by_creator=by_creator
    )
    return report
