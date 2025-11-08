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

class ActivePlanItem(BaseModel):
    id: int
    user_id: int
    plan_id: int
    phone_number: str
    valid_from: datetime
    valid_to: datetime
    status: str

class TopUserItem(BaseModel):
    user_id: Optional[int]
    active_plan_count: int

class CurrentActivePlansReport(BaseModel):
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
