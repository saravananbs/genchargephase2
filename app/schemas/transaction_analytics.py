from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class PeriodStats(BaseModel):
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

class TopUserItem(BaseModel):
    user_id: int
    total_txns: int
    total_amount: float

class TransactionsReport(BaseModel):
    generated_at: datetime
    totals: Dict[str, float]
    period_stats: Dict[str, PeriodStats]
    trends: Dict[str, List[TrendPoint]]
    monthly_trends: Dict[str, List[TrendMonthPoint]]
    distributions: Dict[str, List[DistributionItem]]
    growth_rates: Dict[str, float]
    averages: Dict[str, float]
    top_users: List[TopUserItem] = Field(default_factory=list)
