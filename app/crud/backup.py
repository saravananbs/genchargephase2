# services/backup_service.py
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.backup import Backup
from ..core.database import get_db
import uuid
from datetime import datetime

async def create_backup_record(
    db: AsyncSession,
    backup_data: str,
    snapshot_name: str,
    storage_url: Optional[str] = None,
    backup_status: str = "success",
    size_mb: Optional[int] = None,
    description: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    created_by: Optional[int] = None
) -> Backup:
    """
    Insert a new record into the `Backup` table using async session.
    All fields except `created_at` (auto-filled by DB) are accepted.
    
    Args:
        db (AsyncSession): Async database session
        backup_data (str): Type of data backed up (e.g., "orders", "users")
        snapshot_name (str): Name of the backup file (e.g., "backup_20251107_131200.sql")
        storage_url (str, optional): S3 or file path URL
        backup_status (str): "success" or "failed"
        size_mb (int, optional): Size in MB
        description (str, optional): Human-readable description
        details (dict, optional): Extra JSON metadata
        created_by (int, optional): User ID who triggered backup

    Returns:
        Backup: The created ORM instance
    """
    # Generate unique backup_id if not provided
    backup_id = str(uuid.uuid4())

    # Create new Backup instance
    backup_record = Backup(
        backup_id=backup_id,
        backup_data=backup_data,
        snapshot_name=snapshot_name,
        storage_url=storage_url,
        backup_status=backup_status,
        size_mb=size_mb,
        description=description,
        details=details,
        created_by=created_by
    )

    # Add to session and commit
    db.add(backup_record)
    await db.commit()
    await db.refresh(backup_record)  # Optional: reload with DB-generated values

    return backup_record