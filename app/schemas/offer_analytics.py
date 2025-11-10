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

class OfferItem(BaseModel):
    """Individual offer record information.
    
    Attributes:
        offer_id (int): Unique offer identifier.
        offer_name (str): Name of the offer.
        offer_type_id (Optional[int]): ID of the offer type category.
        is_special (bool): Whether this is a special/featured offer.
        offer_validity (Optional[int]): Validity period in days.
        created_at (Optional[datetime]): When offer was created.
        created_by (Optional[int]): User ID who created the offer.
        status (Optional[str]): Current status (active/inactive).
    """
    offer_id: int
    offer_name: str
    offer_type_id: Optional[int] = None
    is_special: bool
    offer_validity: Optional[int] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    status: Optional[str] = None

class OffersReport(BaseModel):
    """Comprehensive offer analytics and statistics report.
    
    Includes aggregated metrics, trends, distributions, and detailed offer information.
    
    Attributes:
        generated_at (datetime): When this report was generated.
        totals (Dict[str, int]): Aggregate counts (total_offers, special_offers, active, inactive).
        period_counts (Dict[str, PeriodCount]): Offer count breakdown by time period.
        trends (Dict[str, List[TrendPoint]]): Daily trend data for last_7_days, last_30_days.
        monthly_trends (Dict[str, List[TrendMonthPoint]]): Monthly trends for last_6_months, last_1_year.
        distributions (Dict[str, List[DistributionItem]]): Distribution by status, by_offer_type.
        growth_rates (Dict[str, float]): Growth percentage metrics (week_over_week_pct, month_over_month_pct).
        averages (Dict[str, float]): Average metrics (avg_validity_days).
        top_recent_specials (List[OfferItem]): Top special offers created recently.
        offers_by_creator (List[Dict[str, Optional[int]]]): Offer counts grouped by creator user ID.
        offers_by_type_detailed (List[Dict[str, Optional[int]]]): Detailed offer counts by type.
    """
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
