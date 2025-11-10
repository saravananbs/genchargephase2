from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.ext.asyncio import AsyncSession
from ..crud import transaction_analytics as crud_transactions
from ..models.transactions import Transaction
from ..schemas.transaction_analytics import (
    TransactionsReport, PeriodStats, TrendPoint, TrendMonthPoint, DistributionItem, TopUserItem
)

TZ = ZoneInfo("Asia/Kolkata")

def now_tz() -> datetime:
    """
    Return the current datetime localized to the service timezone.

    Returns:
        datetime: Timezone-aware datetime in `Asia/Kolkata`.
    """
    return datetime.now(TZ)

def start_of_day(dt: datetime):
    """
    Compute the start of the day (00:00:00) for a datetime.

    Args:
        dt (datetime): A timezone-aware or naive datetime.

    Returns:
        datetime: Datetime set to the start of the same day.
    """
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt: datetime):
    """
    Compute the end of the day (23:59:59.999999) for a datetime.

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

async def build_transactions_report(db: AsyncSession) -> TransactionsReport:
    """
    Build a transactions analytics report aggregating totals, period stats, trends and distributions.

    Args:
        db (AsyncSession): Database session used to fetch metrics.

    Returns:
        TransactionsReport: Pydantic data structure containing aggregated transaction analytics.

    Raises:
        Any exceptions raised by the underlying CRUD helpers (propagated).
    """
    gen_at = now_tz()

    total_txns = await crud_transactions.total_transactions(db)
    total_amt = await crud_transactions.total_amount(db)
    totals_by_type = await crud_transactions.totals_by_type(db)
    totals_by_status = await crud_transactions.totals_by_status(db)

    totals = {
        "total_transactions": total_txns,
        "total_amount": total_amt,
        "total_credits": totals_by_type.get("credit", {}).get("count", 0),
        "total_debits": totals_by_type.get("debit", {}).get("count", 0),
        "success_count": totals_by_status.get("success", 0),
        "failed_count": totals_by_status.get("failed", 0),
    }

    periods = build_periods()
    period_stats = {}
    for label, (s, e) in periods.items():
        data = await crud_transactions.count_and_amount_between(db, s, e)
        period_stats[label] = PeriodStats(period_label=label, count=data["count"], total_amount=data["total_amount"])

    # Trends
    trend_7d = await crud_transactions.trend_by_day(db, *periods["last_week"])
    trend_30d = await crud_transactions.trend_by_day(db, *periods["last_30_days"])
    trend_6m = await crud_transactions.trend_by_month(db, *periods["last_6_months"])
    trend_12m = await crud_transactions.trend_by_month(db, *periods["last_year"])

    # Distributions
    dist_txn_type = await crud_transactions.distribution_by(Transaction.txn_type, db)
    dist_source = await crud_transactions.distribution_by(Transaction.source, db)
    dist_status = await crud_transactions.distribution_by(Transaction.status, db)
    dist_payment = await crud_transactions.distribution_by(Transaction.payment_method, db)
    dist_service = await crud_transactions.distribution_by(Transaction.service_type, db)
    denom = total_txns or 1

    def make_dist(raw): return [
        DistributionItem(key=r["key"], count=r["count"], percent=round(r["count"]/denom*100, 2)) for r in raw
    ]

    # Growth rates
    prev7_s = periods["last_week"][0] - timedelta(days=7)
    prev7_e = periods["last_week"][0] - timedelta(days=1)
    last7 = await crud_transactions.count_and_amount_between(db, *periods["last_week"])
    prev7 = await crud_transactions.count_and_amount_between(db, prev7_s, prev7_e)
    week_growth = ((last7["count"] - prev7["count"]) / prev7["count"] * 100) if prev7["count"] else 100.0

    prev30_s = periods["last_30_days"][0] - timedelta(days=30)
    prev30_e = periods["last_30_days"][0] - timedelta(days=1)
    last30 = await crud_transactions.count_and_amount_between(db, *periods["last_30_days"])
    prev30 = await crud_transactions.count_and_amount_between(db, prev30_s, prev30_e)
    month_growth = ((last30["count"] - prev30["count"]) / prev30["count"] * 100) if prev30["count"] else 100.0

    # Averages
    avg_amt = await crud_transactions.avg_amount(db)

    # Top Users
    top_users_raw = await crud_transactions.top_users(db)
    top_users = [TopUserItem(**u) for u in top_users_raw]

    return TransactionsReport(
        generated_at=gen_at,
        totals=totals,
        period_stats=period_stats,
        trends={
            "last_7_days": [TrendPoint(**p) for p in trend_7d],
            "last_30_days": [TrendPoint(**p) for p in trend_30d],
        },
        monthly_trends={
            "last_6_months": [TrendMonthPoint(**m) for m in trend_6m],
            "last_1_year": [TrendMonthPoint(**m) for m in trend_12m],
        },
        distributions={
            "by_type": make_dist(dist_txn_type),
            "by_source": make_dist(dist_source),
            "by_status": make_dist(dist_status),
            "by_payment_method": make_dist(dist_payment),
            "by_service_type": make_dist(dist_service),
        },
        growth_rates={
            "week_over_week_pct": round(week_growth, 2),
            "month_over_month_pct": round(month_growth, 2),
        },
        averages={
            "avg_transaction_amount": round(avg_amt, 2),
        },
        top_users=top_users,
    )
