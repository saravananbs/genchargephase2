from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class PeriodCount(BaseModel):
    period_label: str
    count: int

class PeriodSize(BaseModel):
    period_label: str
    total_size_mb: int

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
