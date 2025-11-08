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
    key: Optional[str]
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

# Backup table
class PeriodSize(BaseModel):
    period_label: str
    total_size_mb: int

class TrendMonthPoint(BaseModel):
    month: str
    count: int

class BackupItem(BaseModel):
    backup_id: str
    snapshot_name: Optional[str] = None
    storage_url: Optional[str] = None
    backup_status: Optional[str] = None
    size_mb: Optional[int] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None

class BackupsReport(BaseModel):
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
  

