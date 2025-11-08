from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.ext.asyncio import AsyncSession

from ..crud import referral_analytics as crud_referrals
from ..schemas.referral_analytics import (
    ReferralsReport, PeriodCount, TrendPoint, TrendMonthPoint, DistributionItem, TopReferrerItem
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

async def build_referrals_report(db: AsyncSession) -> ReferralsReport:
    gen_at = now_tz()

    # totals
    total_rewards = await crud_referrals.total_rewards(db)
    total_amount = await crud_referrals.total_reward_amount(db)
    status_data = await crud_referrals.total_by_status(db)
    totals = {
        "total_rewards": total_rewards,
        "total_reward_amount": round(total_amount, 2),
        "pending_rewards": next((s["count"] for s in status_data if s["status"] == "pending"), 0),
        "earned_rewards": next((s["count"] for s in status_data if s["status"] == "earned"), 0)
    }

    # period counts
    periods = build_periods()
    period_counts = {}
    for label, (s, e) in periods.items():
        c = await crud_referrals.count_and_amount_between(db, s, e)
        period_counts[label] = PeriodCount(period_label=label, count=c["count"], total_amount=c["total_amount"])

    # trends
    last7_s, last7_e = periods["last_week"]
    trend_7d = await crud_referrals.trend_by_day(db, last7_s, last7_e)
    last30_s, last30_e = periods["last_30_days"]
    trend_30d = await crud_referrals.trend_by_day(db, last30_s, last30_e)
    trend_6m = await crud_referrals.trend_by_month(db, *periods["last_6_months"])
    trend_12m = await crud_referrals.trend_by_month(db, *periods["last_year"])

    # distributions
    status_dist = [
        DistributionItem(key=s["status"], count=s["count"], percent=round(s["count"] / (total_rewards or 1) * 100, 2))
        for s in status_data
    ]
    amount_dist_raw = await crud_referrals.distribution_by_amount_range(db)
    amount_dist = [
        DistributionItem(key=r["key"], count=r["count"], percent=round(r["count"] / (total_rewards or 1) * 100, 2))
        for r in amount_dist_raw
    ]

    # growth rates
    prev7_s = last7_s - timedelta(days=7)
    prev7_e = last7_s - timedelta(days=1)
    last7 = await crud_referrals.count_and_amount_between(db, last7_s, last7_e)
    prev7 = await crud_referrals.count_and_amount_between(db, prev7_s, prev7_e)
    week_growth = ((last7["count"] - prev7["count"]) / prev7["count"] * 100.0) if prev7["count"] else (100.0 if last7["count"] else 0.0)

    prev30_s = last30_s - timedelta(days=30)
    prev30_e = last30_s - timedelta(days=1)
    last30 = await crud_referrals.count_and_amount_between(db, last30_s, last30_e)
    prev30 = await crud_referrals.count_and_amount_between(db, prev30_s, prev30_e)
    month_growth = ((last30["count"] - prev30["count"]) / prev30["count"] * 100.0) if prev30["count"] else (100.0 if last30["count"] else 0.0)

    # averages
    avg_reward = await crud_referrals.avg_reward_amount(db)
    avg_claim_days = await crud_referrals.avg_claim_time_days(db)

    # top referrers
    top_ref = await crud_referrals.top_referrers(db)
    top_ref_items = [TopReferrerItem(**r) for r in top_ref]

    report = ReferralsReport(
        generated_at=gen_at,
        totals=totals,
        period_counts=period_counts,
        trends={
            "last_7_days": [TrendPoint(**p) for p in trend_7d],
            "last_30_days": [TrendPoint(**p) for p in trend_30d]
        },
        monthly_trends={
            "last_6_months": [TrendMonthPoint(**p) for p in trend_6m],
            "last_1_year": [TrendMonthPoint(**p) for p in trend_12m]
        },
        distributions={
            "by_status": status_dist,
            "by_amount_range": amount_dist
        },
        growth_rates={
            "week_over_week_pct": round(week_growth, 2),
            "month_over_month_pct": round(month_growth, 2)
        },
        averages={
            "avg_reward_amount": round(avg_reward, 2),
            "avg_claim_time_days": round(avg_claim_days, 2)
        },
        top_referrers=top_ref_items
    )
    return report
