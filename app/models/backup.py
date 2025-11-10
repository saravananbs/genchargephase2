from sqlalchemy import Column, String, BigInteger, DateTime, Integer, JSON, Text
from sqlalchemy.sql import func
from ..core.database import Base


class Backup(Base):
    """
    Database backup record model for tracking system backups.

    Attributes:
        backup_id (str): Unique identifier for the backup (primary key).
        backup_data (str): Type of data backed up (e.g., 'product', 'orders', 'users').
        snapshot_name (str): Human-readable snapshot name (e.g., 'backup_2025_10_06_10_00').
        storage_url (str): URL where backup is stored (e.g., S3 path).
        backup_status (str): Status of the backup ('success' or 'failed').
        size_mb (str): Size of the backup in megabytes.
        description (str): Optional description of the backup.
        details (JSON): Additional metadata stored as JSON.
        created_at (DateTime): Timestamp when backup was created (timezone-aware).
        created_by (int): User ID of admin who initiated the backup.
    """
    __tablename__ = "Backup"

    backup_id = Column(String, primary_key=True, index=True)
    backup_data = Column(String, nullable=False, comment="product / orders / users")
    snapshot_name = Column(String, nullable=False, comment="e.g., backup_2025_10_06_10_00")
    storage_url = Column(String, nullable=True, comment="e.g., s3://my-backups/backup_2025_10_06")
    backup_status = Column(String, nullable=False, default="sucess", comment="failed / success")
    size_mb = Column(String, nullable=True, comment="e.g., 104857600")
    description = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=True)
