from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class PeriodStats(BaseModel):
    """Time period statistics with count and amount data.
    
    Attributes:
        period_label (str): Label for the time period (e.g., "2024-01", "Q1").
        count (int): Number of transactions in this period.
        total_amount (float): Total transaction amount in this period.
    """
    period_label: str
    count: int
    total_amount: float

class TrendPoint(BaseModel):
    """Single data point for daily trend analysis with amount.
    
    Attributes:
        date (str): Date of the data point (YYYY-MM-DD format).
        count (int): Count value on this date.
        total_amount (float): Total amount on this date.
    """
    date: str
    count: int
    total_amount: float

class TrendMonthPoint(BaseModel):
    """Single data point for monthly trend analysis with amount.
    
    Attributes:
        month (str): Month label (e.g., "2024-01", "Jan 2024").
        count (int): Count value in this month.
        total_amount (float): Total amount in this month.
    """
    month: str
    count: int
    total_amount: float

class DistributionItem(BaseModel):
    """Distribution breakdown item.
    
    Attributes:
        key (Optional[str]): Category/key for this distribution item.
        count (int): Number of items in this category.
        percent (float): Percentage of total (0-100).
    """
    key: Optional[str]
    count: int
    percent: float

class TopUserItem(BaseModel):
    """Top user by transaction activity.
    
    Attributes:
        user_id (int): ID of the user.
        total_txns (int): Total number of transactions for this user.
        total_amount (float): Total monetary amount of transactions.
    """
    user_id: int
    total_txns: int
    total_amount: float

class TransactionsReport(BaseModel):
    """Comprehensive transaction analytics and statistics report.
    
    Includes transaction volume, revenue trends, distribution, and top users.
    
    Attributes:
        generated_at (datetime): When this report was generated.
        totals (Dict[str, float]): Aggregate amounts (total_revenue, total_refunds, net_revenue, etc).
        period_stats (Dict[str, PeriodStats]): Transaction counts and amounts per time period.
        trends (Dict[str, List[TrendPoint]]): Daily trend data for last_7_days, last_30_days.
        monthly_trends (Dict[str, List[TrendMonthPoint]]): Monthly trends for last_6_months, last_1_year.
        distributions (Dict[str, List[DistributionItem]]): Distribution by_status, by_category, by_payment_method.
        growth_rates (Dict[str, float]): Growth percentage metrics (week_over_week_pct, month_over_month_pct).
        averages (Dict[str, float]): Average metrics (avg_transaction_amount, avg_daily_volume).
        top_users (List[TopUserItem]): Users with most transaction activity.
    """
    generated_at: datetime
    totals: Dict[str, float]
    period_stats: Dict[str, PeriodStats]
    trends: Dict[str, List[TrendPoint]]
    monthly_trends: Dict[str, List[TrendMonthPoint]]
    distributions: Dict[str, List[DistributionItem]]
    growth_rates: Dict[str, float]
    averages: Dict[str, float]
    top_users: List[TopUserItem] = Field(default_factory=list)
