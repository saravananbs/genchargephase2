from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class PeriodCount(BaseModel):
    period_label: str
    count: int
    total_amount: float

class TrendPoint(BaseModel):
    date: str
    count: int
    total_amount: float

class TrendMonthPoint(BaseModel):
    month: str
    count: int
    total_amount: float

class DistributionItem(BaseModel):
    key: Optional[str]
    count: int
    percent: float

class TopReferrerItem(BaseModel):
    referrer_id: int
    total_rewards: int
    total_amount: float

class ReferralsReport(BaseModel):
    generated_at: datetime
    totals: Dict[str, float]
    period_counts: Dict[str, PeriodCount]
    trends: Dict[str, List[TrendPoint]]
    monthly_trends: Dict[str, List[TrendMonthPoint]]
    distributions: Dict[str, List[DistributionItem]]
    growth_rates: Dict[str, float]
    averages: Dict[str, float]
    top_referrers: List[TopReferrerItem] = Field(default_factory=list)
