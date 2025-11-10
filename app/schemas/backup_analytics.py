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

class PeriodSize(BaseModel):
    """Time period with storage size data.
    
    Attributes:
        period_label (str): Label for the time period.
        total_size_mb (int): Total storage size in megabytes for this period.
    """
    period_label: str
    total_size_mb: int

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
    """Comprehensive backup analytics and statistics report.
    
    Includes aggregated metrics, trends, distributions, and detailed backup information.
    
    Attributes:
        generated_at (datetime): When this report was generated.
        totals (Dict[str, int]): Aggregate counts (total_backups, successful, failed, etc).
        period_counts (Dict[str, PeriodCount]): Count breakdown by time period.
        period_sizes (Dict[str, PeriodSize]): Storage size breakdown by time period.
        trends (Dict[str, List[TrendPoint]]): Daily trend data for last_7_days, last_30_days.
        monthly_trends (Dict[str, List[TrendMonthPoint]]): Monthly trends for last_6_months, last_1_year.
        distributions (Dict[str, List[DistributionItem]]): Distribution by status, type, etc.
        growth_rates (Dict[str, float]): Growth percentage metrics (week_over_week, month_over_month).
        last_backup (Optional[BackupItem]): Most recent backup details.
        total_storage_mb (int): Total storage used by all backups.
        avg_backup_size_mb (float): Average backup size in megabytes.
        top_largest_backups (List[BackupItem]): List of largest backups.
        recent_failures (List[BackupItem]): List of recent failed backups.
        backups_by_creator (List[Dict[str, Optional[int]]]): Backup counts grouped by creator user ID.
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
