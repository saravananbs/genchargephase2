from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, List, Optional


# Users table
class ReferrerItem(BaseModel):
    referrer_id: int
    referrer_name: Optional[str] = None
    referred_count: int

class PeriodCount(BaseModel):
    period_label: str
    count: int

class TrendPoint(BaseModel):
    date: str
    count: int

class DistributionItem(BaseModel):
    key: str
    count: int
    percent: float

class UsersReport(BaseModel):
    generated_at: datetime
    totals: Dict[str, int]  # e.g., total_users, active_users, blocked_users
    averages: Dict[str, float]  # e.g., avg_wallet_balance
    period_counts: Dict[str, PeriodCount]  # e.g., 'yesterday': {label, count}
    trends: Dict[str, List[TrendPoint]]  # e.g., 'last_7_days': [{date,count},...]
    distributions: Dict[str, List[DistributionItem]]  # e.g., 'user_type': [...]
    growth_rates: Dict[str, float]  # e.g., week_over_week_pct
    top_referrers: List[ReferrerItem] = Field(default_factory=list)

# Admin table
class AdminItem(BaseModel):
    admin_id: int
    name: Optional[str] = None
    created_at: Optional[datetime] = None

class AdminsReport(BaseModel):
    generated_at: datetime
    totals: Dict[str, int]
    period_counts: Dict[str, PeriodCount]
    trends: Dict[str, List[TrendPoint]]
    distributions: Dict[str, List[DistributionItem]]
    growth_rates: Dict[str, float]

    