# services/backup_service.py
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.backup import Backup
from ..core.database import get_db
from ..core.document_db import get_mongo_db
import uuid
from ..schemas.backup import BackupRestoreLog, BackupRestoreLogCreate
from datetime import datetime

async def create_backup_record(
    db: AsyncSession,
    backup_id: str,
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

async def insert_backup_restore_log(
    log_data: BackupRestoreLogCreate,
    mongo_db = None  # Will use get_mongo_db() if not provided
) -> BackupRestoreLog:
    """
    Insert a backup restore log entry into MongoDB.

    Wraps the internal _insert_log function and manages MongoDB connection context.

    Args:
        log_data (BackupRestoreLogCreate): Log entry data to insert.
        mongo_db (optional): MongoDB client instance. If None, gets connection from get_mongo_db().

    Returns:
        BackupRestoreLog: The inserted log entry with generated ID and timestamp.
    """
    if mongo_db is None:
        async with get_mongo_db() as mongo_db:
            return await _insert_log(log_data, mongo_db)
    else:
        return await _insert_log(log_data, mongo_db)


async def _insert_log(
    log_data: BackupRestoreLogCreate,
    mongo_db: AsyncIOMotorClient
) -> BackupRestoreLog:
    """
    Internal helper to insert a backup restore log into MongoDB.

    Generates a unique log ID and timestamp before insertion.

    Args:
        log_data (BackupRestoreLogCreate): Log entry data to insert.
        mongo_db (AsyncIOMotorClient): MongoDB client instance.

    Returns:
        BackupRestoreLog: The inserted log entry with all fields including generated ID and timestamp.
    """
    collection = mongo_db["BackupRestoreLogs"]

    log_entry = log_data.dict()
    log_entry["log_id"] = str(uuid.uuid4())
    log_entry["created_at"] = datetime.utcnow()

    result = await collection.insert_one(log_entry)
    
    # Return full object
    inserted = await collection.find_one({"_id": result.inserted_id})
    return BackupRestoreLog(**inserted)