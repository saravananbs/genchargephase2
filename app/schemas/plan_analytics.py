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

class PlanItem(BaseModel):
    """Individual plan record information.
    
    Attributes:
        plan_id (int): Unique plan identifier.
        plan_name (str): Name of the plan.
        plan_type (Optional[str]): Type of plan (prepaid/postpaid).
        group_id (Optional[int]): ID of plan group category.
        validity (Optional[int]): Validity period in days.
        price (int): Price of the plan.
        most_popular (bool): Whether this is a popular/featured plan.
        status (Optional[str]): Status (active/inactive).
        created_at (Optional[datetime]): When plan was created.
        created_by (Optional[int]): User ID who created the plan.
    """
    plan_id: int
    plan_name: str
    plan_type: Optional[str] = None
    group_id: Optional[int] = None
    validity: Optional[int] = None
    price: int
    most_popular: bool
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None

class TopPlanActiveCount(BaseModel):
    """Top plans by active subscription count.
    
    Attributes:
        plan_id (int): Unique plan identifier.
        plan_name (Optional[str]): Name of the plan.
        active_count (int): Number of currently active subscriptions.
    """
    plan_id: int
    plan_name: Optional[str] = None
    active_count: int

class PlansReport(BaseModel):
    """Comprehensive plan analytics and statistics report.
    
    Includes aggregated metrics, trends, distributions, and detailed plan information.
    
    Attributes:
        generated_at (datetime): When this report was generated.
        totals (Dict[str, int]): Aggregate counts (total_plans, active_plans_count, inactive_plans_count).
        period_counts (Dict[str, PeriodCount]): Plan count breakdown by time period.
        activation_counts (Dict[str, PeriodCount]): Plan activation counts per period (from CurrentActivePlan.valid_from).
        expiration_counts (Dict[str, PeriodCount]): Plan expiration counts per period (from CurrentActivePlan.valid_to).
        trends (Dict[str, List[TrendPoint]]): Daily trend data for last_7_days, last_30_days.
        monthly_trends (Dict[str, List[TrendMonthPoint]]): Monthly trends for last_6_months, last_1_year.
        distributions (Dict[str, List[DistributionItem]]): Distribution by plan_type, by_status, by_group.
        averages (Dict[str, float]): Average metrics (avg_price, avg_validity).
        growth_rates (Dict[str, float]): Growth percentage metrics (week_over_week_pct, month_over_month_pct).
        most_popular_plans (List[PlanItem]): Top popular plans.
        top_plans_by_active_count (List[TopPlanActiveCount]): Plans with most active subscriptions.
        plans_by_creator (List[Dict[str, Optional[int]]]): Plan counts grouped by creator user ID.
    """
    generated_at: datetime
    totals: Dict[str, int]
    period_counts: Dict[str, PeriodCount]
    activation_counts: Dict[str, PeriodCount]
    expiration_counts: Dict[str, PeriodCount]
    trends: Dict[str, List[TrendPoint]]
    monthly_trends: Dict[str, List[TrendMonthPoint]]
    distributions: Dict[str, List[DistributionItem]]
    averages: Dict[str, float]
    growth_rates: Dict[str, float]
    most_popular_plans: List[PlanItem] = Field(default_factory=list)
    top_plans_by_active_count: List[TopPlanActiveCount] = Field(default_factory=list)
    plans_by_creator: List[Dict[str, Optional[int]]] = Field(default_factory=list)
