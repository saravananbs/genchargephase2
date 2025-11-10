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
    """
    Configuration for backing up a specific table.

    Attributes:
        table_name (AllowedTable): Name of the table to backup.
        date_column (Optional[str]): Column for date filtering (e.g., 'created_at'). Null for full table.
        start_date (Optional[str]): Start date in 'YYYY-MM-DD' format (required if date_column set).
        end_date (Optional[str]): End date in 'YYYY-MM-DD' format (required if date_column set).
    """
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
    """
    Schema for requesting a database backup.

    Attributes:
        backup_data (str): Description/type of data being backed up.
        description (str): Detailed description of the backup.
        tables (List[TableBackupConfig]): List of table backup configurations.
    """
    backup_data: str 
    description: str
    tables: List[TableBackupConfig] = Field(..., description="List of tables with optional date ranges")


class BackupCreateResponse(BaseModel):
    """
    Schema for backup creation response.

    Attributes:
        backup_file (str): Name of the backup file created.
        backup_path (str): Path where backup is stored.
        size_mb (str): Size of backup in megabytes.
        message (str): Status message.
    """
    backup_file: str
    backup_path: str
    size_mb: str
    message: str = "Backup completed successfully"

# Response Models
class BackupResponse(BaseModel):
    """
    Schema for returning backup information in responses.

    Attributes:
        backup_id (str): Unique backup identifier.
        backup_data (str): Type of data backed up.
        snapshot_name (str): Snapshot name.
        storage_url (Optional[str]): URL where backup is stored.
        backup_status (str): Status of backup (success/failed).
        size_mb (Optional[str]): Size in megabytes.
        description (Optional[str]): Backup description.
        details (Optional[List[dict]]): Additional details as JSON.
        created_at (datetime): Creation timestamp.
        created_by (Optional[int]): Admin ID who initiated backup.
    """
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
    """
    Schema for requesting database restore operation.

    Attributes:
        target_db (Optional[str]): Target database for restore (optional, defaults to current).
        clean (bool): Whether to drop existing data before restore.
    """
    target_db: str | None = None  # Optional: restore to different DB
    clean: bool = False           # Drop existing data first

JobType = Literal["backup", "restore", "deleted"]
StatusType = Literal["started", "in_progress", "completed", "failed"]

class TableFilter(BaseModel):
    """
    Schema for filtering tables in backup operations.

    Attributes:
        table_name (str): Name of the table.
        date_column (Optional[str]): Column for date filtering.
        start_date (Optional[str]): Start date in 'YYYY-MM-DD' format.
        end_date (Optional[str]): End date in 'YYYY-MM-DD' format.
    """
    table_name: str
    date_column: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class BackupRestoreLogCreate(BaseModel):
    """
    Schema for creating backup/restore operation logs.

    Attributes:
        job_type (JobType): Type of job (backup/restore/deleted).
        backup_id (str): ID of the backup.
        status (StatusType): Job status (started/in_progress/completed/failed).
        details (Optional[List[TableFilter]]): Table filter details.
        action_by (Optional[int]): Admin ID who initiated the action.
    """
    job_type: JobType
    backup_id: str
    status: StatusType = "started"
    details: Optional[List[TableFilter]] = None
    action_by: Optional[int] = None  # admin_id

class BackupRestoreLog(BackupRestoreLogCreate):
    """
    Schema for backup/restore log information (persisted).

    Attributes:
        log_id (str): Unique log identifier.
        created_at (datetime): Timestamp of log creation.
        (inherits job_type, backup_id, status, details, action_by from BackupRestoreLogCreate)
    """
    log_id: str
    created_at: datetime

    class Config:
        arbitrary_types_allowed=True
        