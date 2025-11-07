from sqlalchemy import Column, String, BigInteger, DateTime, Integer, JSON, Text
from sqlalchemy.sql import func
from ..core.database import Base


class Backup(Base):
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
