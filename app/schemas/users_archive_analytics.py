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

class ArchivedUserItem(BaseModel):
    """Archived user record information.
    
    Attributes:
        user_id (int): Unique user identifier.
        name (Optional[str]): User's full name.
        email (Optional[str]): User's email address.
        phone_number (Optional[str]): User's phone number.
        referral_code (Optional[str]): Referral code generated for user.
        referee_code (Optional[str]): Referral code used during signup.
        user_type (Optional[str]): Type of user (individual/corporate).
        status (Optional[str]): Account status.
        wallet_balance (Optional[float]): Wallet balance at deletion.
        created_at (Optional[datetime]): When account was created.
        deleted_at (Optional[datetime]): When account was deleted.
    """
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
    """Comprehensive archived users analytics and statistics report.
    
    Includes metrics on deleted/archived users, deletion trends, and distributions.
    
    Attributes:
        generated_at (datetime): When this report was generated.
        totals (Dict[str, int]): Aggregate counts (total_archived, etc).
        period_deletions (Dict[str, PeriodCount]): User deletions per time period.
        trends (Dict[str, List[TrendPoint]]): Daily trend data for short ranges.
        monthly_trends (Dict[str, List[TrendMonthPoint]]): Monthly trends for long ranges.
        distributions (Dict[str, List[DistributionItem]]): Distribution by_user_type, by_status.
        averages (Dict[str, float]): Average metrics (avg_wallet_balance, total_wallet_balance).
        growth_rates (Dict[str, float]): Growth percentage metrics.
        top_by_wallet (List[ArchivedUserItem]): Archived users with highest wallet balances.
        recent_deleted (List[ArchivedUserItem]): Recently deleted user accounts.
        phone_number_duplicates (List[Dict[str, int]]): Phone numbers with duplicate archived records.
    """
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
