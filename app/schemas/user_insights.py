from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PaymentMethodStat(BaseModel):
    payment_method: Optional[str]
    total_amount: float

class SourceStat(BaseModel):
    source: Optional[str]
    total_amount: float

class PeriodSpending(BaseModel):
    label: str
    total_spent: float
    txn_count: int

class RechargeNumberCount(BaseModel):
    phone_number: str
    count: int

class TopPlan(BaseModel):
    plan_id: Optional[int]
    plan_name: Optional[str] = None
    usage_count: int

class TopOffer(BaseModel):
    offer_id: Optional[int]
    usage_count: int

class TransactionBreakdown(BaseModel):
    success: int
    failed: int
    pending: int
    credit_count: int
    debit_count: int
    total_amount_spent: float
    total_amount_credited: float

class UserProfileSummary(BaseModel):
    user_id: int
    name: str
    email: str
    user_type: str
    status: str
    wallet_balance: float
    created_at: Optional[datetime]
    account_age_days: int

class UserInsightReport(BaseModel):
    generated_at: datetime
    profile: UserProfileSummary
    transaction_summary: TransactionBreakdown
    spending_by_period: List[PeriodSpending]
    recharge_numbers: List[RechargeNumberCount]
    top_plan: Optional[TopPlan]
    top_offer: Optional[TopOffer]
    top_payment_methods: List[PaymentMethodStat]
    top_sources: List[SourceStat]
    plan_usage_count: int
    avg_recharge_amount: float
    first_txn_date: Optional[datetime]
    last_txn_date: Optional[datetime]
