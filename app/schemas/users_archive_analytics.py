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

class ArchivedUserItem(BaseModel):
    user_id: int
    name: Optional[str]
    email: Optional[str]
    phone_number: Optional[str]
    referral_code: Optional[str]
    referee_code: Optional[str]
    user_type: Optional[str]
    status: Optional[str]
    wallet_balance: Optional[float]
    created_at: Optional[datetime]
    deleted_at: Optional[datetime]

class UsersArchiveReport(BaseModel):
    generated_at: datetime
    totals: Dict[str, int]
    period_deletions: Dict[str, PeriodCount]
    trends: Dict[str, List[TrendPoint]]           # daily trends for short ranges
    monthly_trends: Dict[str, List[TrendMonthPoint]]  # monthly for long ranges
    distributions: Dict[str, List[DistributionItem]]  # by_user_type, by_status
    averages: Dict[str, float]               # avg_wallet_balance, total_wallet_balance
    growth_rates: Dict[str, float]
    top_by_wallet: List[ArchivedUserItem] = Field(default_factory=list)
    recent_deleted: List[ArchivedUserItem] = Field(default_factory=list)
    phone_number_duplicates: List[Dict[str, int]] = Field(default_factory=list)
