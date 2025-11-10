from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, List, Optional


# Users table
class ReferrerItem(BaseModel):
    """Referrer information for user analytics.
    
    Attributes:
        referrer_id (int): ID of the referrer user.
        referrer_name (Optional[str]): Name of the referrer.
        referred_count (int): Number of users referred by this person.
    """
    referrer_id: int
    referrer_name: Optional[str] = None
    referred_count: int

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

class UsersReport(BaseModel):
    """Comprehensive users analytics and statistics report.
    
    Includes user metrics, trends, distributions, and top referrers.
    
    Attributes:
        generated_at (datetime): When this report was generated.
        totals (Dict[str, int]): Aggregate counts (total_users, active_users, blocked_users).
        averages (Dict[str, float]): Average metrics (avg_wallet_balance).
        period_counts (Dict[str, PeriodCount]): User counts per time period.
        trends (Dict[str, List[TrendPoint]]): Daily trend data for last_7_days, last_30_days.
        distributions (Dict[str, List[DistributionItem]]): Distribution by_user_type, by_status.
        growth_rates (Dict[str, float]): Growth percentage metrics (week_over_week_pct, month_over_month_pct).
        top_referrers (List[ReferrerItem]): Top users by referral count.
    """
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
    """Admin record information for analytics.
    
    Attributes:
        admin_id (int): Unique admin identifier.
        name (Optional[str]): Admin's full name.
        created_at (Optional[datetime]): When admin account was created.
    """
    admin_id: int
    name: Optional[str] = None
    created_at: Optional[datetime] = None

class AdminsReport(BaseModel):
    """Comprehensive admins analytics and statistics report.
    
    Includes admin metrics, trends, and distributions.
    
    Attributes:
        generated_at (datetime): When this report was generated.
        totals (Dict[str, int]): Aggregate admin counts.
        period_counts (Dict[str, PeriodCount]): Admin counts per time period.
        trends (Dict[str, List[TrendPoint]]): Daily trend data.
        distributions (Dict[str, List[DistributionItem]]): Distribution by role, status.
        growth_rates (Dict[str, float]): Growth percentage metrics.
    """
    generated_at: datetime
    totals: Dict[str, int]
    period_counts: Dict[str, PeriodCount]
    trends: Dict[str, List[TrendPoint]]
    distributions: Dict[str, List[DistributionItem]]
    growth_rates: Dict[str, float]

# Backup table
class PeriodSize(BaseModel):
    """Time period with storage size data.
    
    Attributes:
        period_label (str): Label for the time period.
        total_size_mb (int): Total storage size in megabytes for this period.
    """
    period_label: str
    total_size_mb: int

class TrendMonthPoint(BaseModel):
    """Single data point for monthly trend analysis.
    
    Attributes:
        month (str): Month label (e.g., "2024-01", "Jan 2024").
        count (int): Count value in this month.
    """
    month: str
    count: int

class BackupItem(BaseModel):
    """Individual backup record information.
    
    Attributes:
        backup_id (str): Unique backup identifier.
        snapshot_name (Optional[str]): Name of the backup snapshot.
        storage_url (Optional[str]): URL or path to the stored backup.
        backup_status (Optional[str]): Status of the backup (success/failed/partial).
        size_mb (Optional[int]): Size of backup in megabytes.
        created_at (Optional[datetime]): When backup was created.
        created_by (Optional[int]): User ID who initiated the backup.
    """
    backup_id: str
    snapshot_name: Optional[str] = None
    storage_url: Optional[str] = None
    backup_status: Optional[str] = None
    size_mb: Optional[int] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None

class BackupsReport(BaseModel):
    """Comprehensive backups analytics and statistics report.
    
    Includes backup metrics, storage trends, and distributions.
    
    Attributes:
        generated_at (datetime): When this report was generated.
        totals (Dict[str, int]): Aggregate backup counts.
        period_counts (Dict[str, PeriodCount]): Backup counts per time period.
        period_sizes (Dict[str, PeriodSize]): Storage size breakdown by time period.
        trends (Dict[str, List[TrendPoint]]): Daily trend data.
        monthly_trends (Dict[str, List[TrendMonthPoint]]): Monthly trends.
        distributions (Dict[str, List[DistributionItem]]): Distribution by status.
        growth_rates (Dict[str, float]): Growth percentage metrics.
        last_backup (Optional[BackupItem]): Most recent backup details.
        total_storage_mb (int): Total storage used by all backups.
        avg_backup_size_mb (float): Average backup size in megabytes.
    """
    generated_at: datetime
    totals: Dict[str, int]
    period_counts: Dict[str, PeriodCount]
    period_sizes: Dict[str, PeriodSize]
    trends: Dict[str, List[TrendPoint]]
    monthly_trends: Dict[str, List[TrendMonthPoint]]
    distributions: Dict[str, List[DistributionItem]]
    growth_rates: Dict[str, float]
    last_backup: Optional[BackupItem] = None
    total_storage_mb: int
    avg_backup_size_mb: float
    top_largest_backups: List[BackupItem] = Field(default_factory=list)
    recent_failures: List[BackupItem] = Field(default_factory=list)
    backups_by_creator: List[Dict[str, Optional[int]]] = Field(default_factory=list)
  

