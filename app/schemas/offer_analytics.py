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

class OfferItem(BaseModel):
    offer_id: int
    offer_name: str
    offer_type_id: Optional[int] = None
    is_special: bool
    offer_validity: Optional[int] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    status: Optional[str] = None

class OffersReport(BaseModel):
    generated_at: datetime
    totals: Dict[str, int]                           # total_offers, special_offers
    period_counts: Dict[str, PeriodCount]            # counts per period
    trends: Dict[str, List[TrendPoint]]              # last_7_days, last_30_days
    monthly_trends: Dict[str, List[TrendMonthPoint]] # last_6_months, last_1_year
    distributions: Dict[str, List[DistributionItem]] # by_status, by_offer_type
    growth_rates: Dict[str, float]                   # week_over_week_pct, month_over_month_pct
    averages: Dict[str, float]                       # avg_validity_days
    top_recent_specials: List[OfferItem] = Field(default_factory=list)
    offers_by_creator: List[Dict[str, Optional[int]]] = Field(default_factory=list)
    offers_by_type_detailed: List[Dict[str, Optional[int]]] = Field(default_factory=list)
