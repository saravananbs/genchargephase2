from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from ..crud import offer_analytics as crud_offers
from ..schemas.offer_analytics import (
    OffersReport, PeriodCount, TrendPoint, TrendMonthPoint, DistributionItem, OfferItem
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

async def build_offers_report(db: AsyncSession) -> OffersReport:
    """
    Build a comprehensive offers analytics report aggregating counts, trends, distributions and growth metrics.

    Args:
        db (AsyncSession): Database session used to fetch aggregate metrics.

    Returns:
        OffersReport: Pydantic data structure containing analytics for offers.

    Raises:
        Any exceptions raised by the underlying CRUD helper functions (propagated).
    """
    gen_at = now_tz()

    total = await crud_offers.total_offers(db)
    totals = {
        "total_offers": total,
        "special_offers": await crud_offers.count_special_between(db, *build_periods()["last_year"])  # count special in last year as sample
    }

    periods = build_periods()
    period_counts = {}
    for label, (s, e) in periods.items():
        cnt = await crud_offers.count_between(db, s, e)
        period_counts[label] = PeriodCount(period_label=label, count=cnt)

    # trends
    last7_s, last7_e = periods["last_week"]
    trend_7d = await crud_offers.trend_by_day(db, last7_s, last7_e)

    last30_s, last30_e = periods["last_30_days"]
    trend_30d = await crud_offers.trend_by_day(db, last30_s, last30_e)

    trend_6m = await crud_offers.trend_by_month(db, *periods["last_6_months"])
    trend_12m = await crud_offers.trend_by_month(db, *periods["last_year"])

    # distributions
    status_raw = await crud_offers.distribution_by_status(db)
    type_raw = await crud_offers.distribution_by_offer_type(db)
    denom = total or 1
    status_dist = [DistributionItem(key=r["key"], count=r["count"], percent=round(r["count"]/denom*100.0, 2)) for r in status_raw]
    type_dist = [DistributionItem(key=r["key"], count=r["count"], percent=round(r["count"]/denom*100.0, 2)) for r in type_raw]

    # growth rates (wk/wk and mo/mo) - compare last week vs previous week
    prev7_s = last7_s - timedelta(days=7); prev7_e = last7_s - timedelta(days=1)
    last7_cnt = await crud_offers.count_between(db, last7_s, last7_e)
    prev7_cnt = await crud_offers.count_between(db, prev7_s, prev7_e)
    week_over_week_pct = ((last7_cnt - prev7_cnt) / prev7_cnt * 100.0) if prev7_cnt else (100.0 if last7_cnt else 0.0)

    prev30_s = last30_s - timedelta(days=30); prev30_e = last30_s - timedelta(days=1)
    last30_cnt = await crud_offers.count_between(db, last30_s, last30_e)
    prev30_cnt = await crud_offers.count_between(db, prev30_s, prev30_e)
    month_over_month_pct = ((last30_cnt - prev30_cnt) / prev30_cnt * 100.0) if prev30_cnt else (100.0 if last30_cnt else 0.0)

    # averages & extras
    avg_validity = await crud_offers.avg_validity(db)
    top_specials = await crud_offers.top_recent_specials(db, limit=10)
    by_creator = await crud_offers.offers_by_creator(db)
    by_type_details = await crud_offers.offers_by_type_detailed(db)

    report = OffersReport(
        generated_at=gen_at,
        totals=totals,
        period_counts=period_counts,
        trends={
            "last_7_days": [TrendPoint(**p) for p in trend_7d],
            "last_30_days": [TrendPoint(**p) for p in trend_30d]
        },
        monthly_trends={
            "last_6_months": [TrendMonthPoint(month=m["month"], count=m["count"]) for m in trend_6m],
            "last_1_year": [TrendMonthPoint(month=m["month"], count=m["count"]) for m in trend_12m]
        },
        distributions={
            "by_status": status_dist,
            "by_offer_type": type_dist
        },
        growth_rates={
            "week_over_week_pct": round(week_over_week_pct, 2),
            "month_over_month_pct": round(month_over_month_pct, 2)
        },
        averages={
            "avg_validity_days": round(avg_validity, 2)
        },
        top_recent_specials=[OfferItem(**o) for o in top_specials],
        offers_by_creator=by_creator,
        offers_by_type_detailed=by_type_details
    )
    return report
