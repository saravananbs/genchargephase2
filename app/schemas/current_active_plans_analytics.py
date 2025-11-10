from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class PeriodCount(BaseModel):
    """Time period with count data.
    
    Attributes:
        period_label (str): Label for the time period (e.g., "2024-01", "Q1").
        count (int): Number of items in this period.
    """
    period_label: str
    count: int

class TrendPoint(BaseModel):
    """Single data point for daily trend analysis.
    
    Attributes:
        date (str): Date of the data point (YYYY-MM-DD format).
        count (int): Count value on this date.
    """
    date: str
    count: int

class TrendMonthPoint(BaseModel):
    """Single data point for monthly trend analysis.
    
    Attributes:
        month (str): Month label (e.g., "2024-01", "Jan 2024").
        count (int): Count value in this month.
    """
    month: str
    count: int

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

class ActivePlanItem(BaseModel):
    """Individual active plan subscription record.
    
    Attributes:
        id (int): Unique subscription record ID.
        user_id (int): ID of the user who owns this plan.
        plan_id (int): ID of the subscribed plan.
        phone_number (str): Associated phone number.
        valid_from (datetime): When the plan becomes active.
        valid_to (datetime): When the plan expires.
        status (str): Current subscription status.
    """
    id: int
    user_id: int
    plan_id: int
    phone_number: str
    valid_from: datetime
    valid_to: datetime
    status: str

class TopUserItem(BaseModel):
    """User with their active plan count.
    
    Attributes:
        user_id (Optional[int]): ID of the user.
        active_plan_count (int): Number of active plans for this user.
    """
    user_id: Optional[int]
    active_plan_count: int

class CurrentActivePlansReport(BaseModel):
    """Comprehensive current active plans analytics and statistics report.
    
    Includes subscription metrics, activation/expiration trends, and user insights.
    
    Attributes:
        generated_at (datetime): When this report was generated.
        totals (Dict[str, int]): Aggregate counts (total_active, total_expired, etc).
        period_activations (Dict[str, PeriodCount]): New activations per time period.
        period_expirations (Dict[str, PeriodCount]): Expirations per time period.
        trends (Dict[str, List[TrendPoint]]): Daily trend data for last_7_days, last_30_days.
        monthly_trends (Dict[str, List[TrendMonthPoint]]): Monthly trends for last_6_months, last_1_year.
        distributions (Dict[str, List[DistributionItem]]): Distribution by_status, by_plan.
        growth_rates (Dict[str, float]): Growth percentage metrics.
        avg_plan_duration_days (float): Average duration of active plans in days.
        upcoming_expirations (List[ActivePlanItem]): Plans expiring soon.
        top_users (List[TopUserItem]): Users with most active plans.
        phone_number_duplicates (List[Dict[str, int]]): Phone numbers with multiple active plans.
    """
    generated_at: datetime
    totals: Dict[str, int]
    period_activations: Dict[str, PeriodCount]
    period_expirations: Dict[str, PeriodCount]
    trends: Dict[str, List[TrendPoint]]            # last_7_days, last_30_days
    monthly_trends: Dict[str, List[TrendMonthPoint]]  # last_6_months, last_1_year
    distributions: Dict[str, List[DistributionItem]]  # by_status, by_plan
    growth_rates: Dict[str, float]
    avg_plan_duration_days: float
    upcoming_expirations: List[ActivePlanItem] = Field(default_factory=list)
    top_users: List[TopUserItem] = Field(default_factory=list)
    phone_number_duplicates: List[Dict[str, int]] = Field(default_factory=list)
