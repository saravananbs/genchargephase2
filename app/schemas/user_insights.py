from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PaymentMethodStat(BaseModel):
    """Payment method usage statistics.
    
    Attributes:
        payment_method (Optional[str]): Name of the payment method.
        total_amount (float): Total amount transacted via this payment method.
    """
    payment_method: Optional[str]
    total_amount: float

class SourceStat(BaseModel):
    """Transaction source statistics.
    
    Attributes:
        source (Optional[str]): Name of the transaction source (recharge/autopay/referral).
        total_amount (float): Total amount from this source.
    """
    source: Optional[str]
    total_amount: float

class PeriodSpending(BaseModel):
    """User spending data for a time period.
    
    Attributes:
        label (str): Period label (month/quarter/year).
        total_spent (float): Total spending in this period.
        txn_count (int): Number of transactions in this period.
    """
    label: str
    total_spent: float
    txn_count: int

class RechargeNumberCount(BaseModel):
    """Recharge frequency by phone number.
    
    Attributes:
        phone_number (str): Phone number that was recharged.
        count (int): Number of recharges for this number.
    """
    phone_number: str
    count: int

class TopPlan(BaseModel):
    """Most frequently used plan by user.
    
    Attributes:
        plan_id (Optional[int]): ID of the plan.
        plan_name (Optional[str]): Name of the plan.
        usage_count (int): Number of times this plan was subscribed.
    """
    plan_id: Optional[int]
    plan_name: Optional[str] = None
    usage_count: int

class TopOffer(BaseModel):
    """Most frequently used offer by user.
    
    Attributes:
        offer_id (Optional[int]): ID of the offer.
        usage_count (int): Number of times this offer was applied.
    """
    offer_id: Optional[int]
    usage_count: int

class TransactionBreakdown(BaseModel):
    """Summary of user transactions by type and status.
    
    Attributes:
        success (int): Number of successful transactions.
        failed (int): Number of failed transactions.
        pending (int): Number of pending transactions.
        credit_count (int): Number of credit transactions.
        debit_count (int): Number of debit transactions.
        total_amount_spent (float): Total amount spent in debit transactions.
        total_amount_credited (float): Total amount credited in credit transactions.
    """
    success: int
    failed: int
    pending: int
    credit_count: int
    debit_count: int
    total_amount_spent: float
    total_amount_credited: float

class UserProfileSummary(BaseModel):
    """User profile and account information summary.
    
    Attributes:
        user_id (int): Unique user identifier.
        name (str): User's full name.
        email (str): User's email address.
        user_type (str): Type of user (individual/corporate/admin).
        status (str): Current account status (active/suspended/inactive).
        wallet_balance (float): Current wallet balance.
        created_at (Optional[datetime]): Account creation timestamp.
        account_age_days (int): Number of days the account has existed.
    """
    user_id: int
    name: str
    email: str
    user_type: str
    status: str
    wallet_balance: float
    created_at: Optional[datetime]
    account_age_days: int

class UserInsightReport(BaseModel):
    """Comprehensive user insights and analytics report.
    
    Includes profile summary, transaction breakdown, spending patterns, and usage preferences.
    
    Attributes:
        generated_at (datetime): When this report was generated.
        profile (UserProfileSummary): User profile and account info.
        transaction_summary (TransactionBreakdown): Summary of transactions by type/status.
        spending_by_period (List[PeriodSpending]): Spending broken down by time periods.
        recharge_numbers (List[RechargeNumberCount]): Recharge frequency for each phone number.
        top_plan (Optional[TopPlan]): Most frequently used plan.
        top_offer (Optional[TopOffer]): Most frequently used offer.
        top_payment_methods (List[PaymentMethodStat]): Top payment methods by amount.
        top_sources (List[SourceStat]): Top transaction sources by amount.
        plan_usage_count (int): Total number of plan subscriptions.
        avg_recharge_amount (float): Average amount per recharge transaction.
        first_txn_date (Optional[datetime]): Date of first transaction.
        last_txn_date (Optional[datetime]): Date of last transaction.
    """
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
