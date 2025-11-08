from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class PeriodCount(BaseModel):
    period_label: str
    count: int

class TrendPoint(BaseModel):
    date: str
    count: int

class TrendMonthPoint(BaseModel):
    month: str
    count: int

class DistributionItem(BaseModel):
    key: Optional[str]
    count: int
    percent: float

class PlanItem(BaseModel):
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
    plan_id: int
    plan_name: Optional[str] = None
    active_count: int

class PlansReport(BaseModel):
    generated_at: datetime
    totals: Dict[str, int]                 # total_plans, active_plans_count, inactive_plans_count
    period_counts: Dict[str, PeriodCount]
    activation_counts: Dict[str, PeriodCount]   # activations per period (from CurrentActivePlan.valid_from)
    expiration_counts: Dict[str, PeriodCount]   # expirations per period (from CurrentActivePlan.valid_to)
    trends: Dict[str, List[TrendPoint]]         # daily trends for last_7 and last_30
    monthly_trends: Dict[str, List[TrendMonthPoint]]  # last_6_months, last_1_year
    distributions: Dict[str, List[DistributionItem]]  # by_plan_type, by_status, by_group
    averages: Dict[str, float]               # avg_price, avg_validity
    growth_rates: Dict[str, float]           # week_over_week_pct, month_over_month_pct
    most_popular_plans: List[PlanItem] = Field(default_factory=list)
    top_plans_by_active_count: List[TopPlanActiveCount] = Field(default_factory=list)
    plans_by_creator: List[Dict[str, Optional[int]]] = Field(default_factory=list)
