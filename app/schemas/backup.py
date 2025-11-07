from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

AllowedTable = Literal[
    "Sessions",
    "TokenRevocation",
    "Plans",
    "Users",
    "PlanGroups",
    "Transactions",
    "Roles",
    "Admins",
    "Permissions",
    "RolePermissions",
    "CurrentActivePlans",
    "OfferTypes",
    "Offers",
    "ReferralRewards",
    "UsersArchieve",
    "UserPreferences",
    "AutoPay",
    "Backup",
]

class TableBackupConfig(BaseModel):
    table_name: AllowedTable = Field(..., description="Name of the table to backup")
    date_column: Optional[str] = Field(
        None,
        description="Column name for date filtering (e.g., 'created_at'). "
                    "Set to null for full table backup."
    )
    start_date: Optional[str] = Field(
        None,
        description="Start date in 'YYYY-MM-DD' format. Required if date_column is set."
    )
    end_date: Optional[str] = Field(
        None,
        description="End date in 'YYYY-MM-DD' format. Required if date_column is set."
    )


class BackupRequest(BaseModel):
    backup_data: str 
    description: str
    tables: List[TableBackupConfig] = Field(..., description="List of tables with optional date ranges")


class BackupCreateResponse(BaseModel):
    backup_file: str
    backup_path: str
    size_mb: str
    message: str = "Backup completed successfully"

# Response Models
class BackupResponse(BaseModel):
    backup_id: str
    backup_data: str
    snapshot_name: str
    storage_url: str | None
    backup_status: str
    size_mb: str | None
    description: str | None
    details: List[dict] | None
    created_at: datetime
    created_by: int | None

    class Config:
        arbitrary_types_allowed=True
        from_attributes = True


class RestoreRequest(BaseModel):
    target_db: str | None = None  # Optional: restore to different DB
    clean: bool = False           # Drop existing data first

JobType = Literal["backup", "restore", "deleted"]
StatusType = Literal["started", "in_progress", "completed", "failed"]

class TableFilter(BaseModel):
    table_name: str
    date_column: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class BackupRestoreLogCreate(BaseModel):
    job_type: JobType
    backup_id: str
    status: StatusType = "started"
    details: Optional[List[TableFilter]] = None
    action_by: Optional[int] = None  # admin_id

class BackupRestoreLog(BackupRestoreLogCreate):
    log_id: str
    created_at: datetime

    class Config:
        arbitrary_types_allowed=True
        