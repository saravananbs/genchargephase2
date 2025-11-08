from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.ext.asyncio import AsyncSession

from ..crud import user_insights as crud_user_insights
from ..schemas.user_insights import (
    UserInsightReport, UserProfileSummary, TransactionBreakdown,
    PeriodSpending, RechargeNumberCount, TopPlan, TopOffer
)

TZ = ZoneInfo("Asia/Kolkata")

async def build_user_insight_report(db: AsyncSession, user_id: int) -> UserInsightReport:
    gen_at = datetime.now(TZ)

    profile_data = await crud_user_insights.get_user_profile(db, user_id)
    if not profile_data:
        raise ValueError(f"User {user_id} not found")

    txn_summary_data = await crud_user_insights.transaction_summary(db, user_id)
    spending_periods = await crud_user_insights.spending_by_period(db, user_id)
    recharge_numbers = await crud_user_insights.recharge_numbers(db, user_id)
    top_plan = await crud_user_insights.most_used_plan(db, user_id)
    top_offer = await crud_user_insights.most_used_offer(db, user_id)
    pay_methods = await crud_user_insights.top_payment_methods(db, user_id)
    sources = await crud_user_insights.top_sources(db, user_id)
    timeline = await crud_user_insights.user_transaction_timeline(db, user_id)

    return UserInsightReport(
        generated_at=gen_at,
        profile=UserProfileSummary(**profile_data),
        transaction_summary=TransactionBreakdown(**txn_summary_data),
        spending_by_period=[PeriodSpending(**p) for p in spending_periods],
        recharge_numbers=[RechargeNumberCount(**n) for n in recharge_numbers],
        top_plan=(TopPlan(**top_plan) if top_plan else None),
        top_offer=(TopOffer(**top_offer) if top_offer else None),
        top_payment_methods=pay_methods,
        top_sources=sources,
        plan_usage_count=len(recharge_numbers),
        avg_recharge_amount=round(txn_summary_data["total_amount_spent"] / (txn_summary_data["debit_count"] or 1), 2),
        first_txn_date=timeline["first"],
        last_txn_date=timeline["last"]
    )
