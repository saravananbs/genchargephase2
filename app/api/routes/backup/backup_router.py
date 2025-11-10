# routers/backup.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Security
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from ....models.backup import Backup
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes
from ....schemas.backup import BackupRequest, BackupResponse, BackupCreateResponse, RestoreRequest, BackupRestoreLogCreate, TableFilter
from ....models.admins import Admin
from ....services.backup import perform_pg_dump_backup_async, run_pg_restore
from ....core.database import get_db
from ....core.document_db import get_mongo_db
from ....crud.backup import insert_backup_restore_log
import asyncio
import datetime
import shutil
import os 
import logging
import uuid
from ....crud.backup import create_backup_record

router = APIRouter(prefix="/backup", tags=["Backup"])
logger = logging.getLogger(__name__)

@router.post("/create", response_model=BackupCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_backup(
    request: BackupRequest,
    db = Depends(get_db),
    mongo_db = Depends(get_mongo_db),
    current_user: Admin = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Backup:write"])
):
    """
    Create a new database backup with optional date range filtering.
    
    Initiates a PostgreSQL dump backup operation for specified tables with optional
    filtering by date columns and ranges. Uses pg_dump for consistent, reliable
    backups. Backup file is stored on disk and metadata recorded in database.
    
    Security:
        - Requires valid JWT access token
        - Scope: Backup:write
        - Only admins can initiate backups
        - Requires storage permissions on server
    
    Request Body:
        BackupRequest (JSON):
            - tables (list): Array of table objects to backup:
                - table_name (str): Name of table to backup (required)
                - date_column (str, optional): Column to filter by date range
                - start_date (datetime, optional): Filter start date (ISO format)
                - end_date (datetime, optional): Filter end date (ISO format)
            - backup_data (str, optional): Custom backup label/metadata
            - description (str, optional): Human-readable backup description
    
    Returns:
        BackupCreateResponse:
            - backup_file (str): Generated backup filename
            - backup_path (str): Full file path on disk
            - size_mb (float): Backup file size in megabytes
    
    Raises:
        HTTPException(400): Invalid table names or date range parameters
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Backup:write scope
        HTTPException(500): pg_dump execution failed or disk write error
    
    Example:
        Request:
            POST /backup/create
            Headers: Authorization: Bearer <jwt_token>
            Body:
            {
                "tables": [
                    {
                        "table_name": "transactions",
                        "date_column": "created_at",
                        "start_date": "2024-01-01T00:00:00Z",
                        "end_date": "2024-01-31T23:59:59Z"
                    },
                    {
                        "table_name": "users"
                    }
                ],
                "description": "Monthly backup for January 2024"
            }
        
        Response (201 Created):
            {
                "backup_file": "backup_20240120_143000.sql",
                "backup_path": "/backups/backup_20240120_143000.sql",
                "size_mb": 245.67
            }
    """
    # Convert to expected dict format
    table_date_ranges = [
        {
            "table_name": t.table_name,
            "date_column": t.date_column,
            "start_date": t.start_date,
            "end_date": t.end_date
        }
        for t in request.tables
    ]
    backup_id = str(uuid.uuid4())
    log = BackupRestoreLogCreate(
        job_type="backup",
        backup_id=backup_id,
        status="started",
        details=[
            TableFilter(
                table_name=t["table_name"],
                date_column=t.get("date_column"),
                start_date=t.get("start_date"),
                end_date=t.get("end_date")
            )
            for t in table_date_ranges
        ],
        action_by=current_user.admin_id
    )
    await insert_backup_restore_log(mongo_db=mongo_db,log_data=log)
    try:
        result = await perform_pg_dump_backup_async(
            table_date_ranges=table_date_ranges,
            db_session=db
        )
        if result:
            await insert_backup_restore_log(mongo_db=mongo_db, log_data=BackupRestoreLogCreate(
                job_type="backup",
                backup_id=log.backup_id,
                status="completed",
                details=log.details,
                action_by=current_user.admin_id
            ))
        else:
            await insert_backup_restore_log(mongo_db=mongo_db, log_data=BackupRestoreLogCreate(
                job_type="backup",
                backup_id="failed",
                status="failed",
                details=log.details,
                action_by=current_user.admin_id
            ))

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Backup failed. Check server logs or pg_dump permissions."
            )
        await create_backup_record(
            db=db,
            backup_id = backup_id,
            backup_data=request.backup_data, snapshot_name=result["backup_file"],
            storage_url=result["backup_path"], size_mb=result["size_mb"],
            description=request.description, details=table_date_ranges, created_by=current_user.admin_id)
        return BackupCreateResponse(
            backup_file=result["backup_file"],
            backup_path=result["backup_path"],
            size_mb=result["size_mb"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup process error: {str(e)}"
        )
    

# 1. GET ALL BACKUPS
@router.get("/", response_model=List[BackupResponse])
async def list_backups(db: AsyncSession = Depends(get_db), 
    current_user: Admin = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Backup:read"])
):
    """
    List all backup records with creation and size details.
    
    Retrieves a comprehensive list of all database backups that have been created
    in the system. Shows backup metadata including timestamps, file sizes, tables
    included, and backup status. Ordered by most recent first.
    
    Security:
        - Requires valid JWT access token
        - Scope: Backup:read
        - Typically restricted to super-admin or platform admin
    
    Returns:
        List[BackupResponse]: Array of backup objects, each containing:
            - backup_id (str): Unique backup identifier (UUID)
            - backup_file (str): Filename of backup
            - storage_url (str): Full path to backup file
            - size_mb (float): Backup file size in megabytes
            - description (str): Human-readable description
            - tables (list): Tables included in backup
            - created_at (datetime): When backup was created
            - created_by (int): Admin ID who initiated backup
            - status (str): Backup status (completed, failed, partial)
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Backup:read scope
    
    Example:
        Request:
            GET /backup/
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            [
                {
                    "backup_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                    "backup_file": "backup_20240120_143000.sql",
                    "storage_url": "/backups/backup_20240120_143000.sql",
                    "size_mb": 245.67,
                    "description": "Monthly backup for January 2024",
                    "tables": ["transactions", "users", "plans"],
                    "created_at": "2024-01-20T14:30:00Z",
                    "created_by": 1,
                    "status": "completed"
                },
                {
                    "backup_id": "e38ad214-d6ae-4f31-83e6-1a2b3c4d5e6f",
                    "backup_file": "backup_20240119_100000.sql",
                    "storage_url": "/backups/backup_20240119_100000.sql",
                    "size_mb": 198.45,
                    "description": "Daily backup",
                    "tables": ["transactions"],
                    "created_at": "2024-01-19T10:00:00Z",
                    "created_by": 1,
                    "status": "completed"
                }
            ]
    """
    result = await db.execute(select(Backup).order_by(Backup.created_at.desc()))
    backups = result.scalars().all()
    return backups


# 2. DELETE BACKUP BY ID
@router.delete("/{backup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup(
    backup_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    mongo_db = Depends(get_mongo_db),
    current_user: Admin = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Backup:delete"])
):
    """
    Delete a backup record and optionally remove the backup file.
    
    Removes a backup record from the system and optionally deletes the physical
    backup file from disk. This action is permanent and cannot be undone.
    Deletion is logged for audit purposes. File removal is done asynchronously
    to avoid blocking the response.
    
    Security:
        - Requires valid JWT access token
        - Scope: Backup:delete
        - Only super-admin can delete backups
        - Action is logged in audit trail
    
    Path Parameters:
        - backup_id (str): UUID of backup to delete (must exist)
    
    Returns:
        None: HTTP 204 No Content (successful deletion)
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Backup:delete scope
        HTTPException(404): Backup with given ID not found
        HTTPException(500): Database or disk operation failed
    
    Example:
        Request:
            DELETE /backup/f47ac10b-58cc-4372-a567-0e02b2c3d479
            Headers: Authorization: Bearer <jwt_token>
        
        Response (204 No Content):
            (empty body)
    """
    result = await db.execute(select(Backup).where(Backup.backup_id == backup_id))
    backup = result.scalar_one_or_none()

    log = BackupRestoreLogCreate(
        job_type="deleted",
        backup_id=backup.backup_id,
        status="completed",
        details=backup.details,
        action_by=current_user.admin_id
    )

    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    # Optional: Delete physical file in background
    if backup.storage_url and os.path.exists(backup.storage_url):
        background_tasks.add_task(shutil.rmtree if os.path.isdir(backup.storage_url) else os.remove, backup.storage_url)
    
    # Delete from DB
    await db.execute(delete(Backup).where(Backup.backup_id == backup_id))
    await db.commit()
    
    await insert_backup_restore_log(mongo_db=mongo_db,log_data=log)
    return None


# 3. RESTORE BACKUP BY ID
@router.post("/{backup_id}/restore", status_code=status.HTTP_202_ACCEPTED)
async def restore_backup(
    backup_id: str,
    request: RestoreRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    mongo_db = Depends(get_mongo_db),
    current_user: Admin = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Backup:edit"])
):
    """
    Restore database from backup using pg_restore.
    
    Initiates an asynchronous restore operation using PostgreSQL pg_restore utility.
    Restores data from a previously created backup file into a target database.
    Supports optional cleaning of existing data before restore. Long-running
    operation runs in background; returns 202 Accepted immediately with job status.
    
    Security:
        - Requires valid JWT access token
        - Scope: Backup:edit
        - Only super-admin can restore backups
        - Restore operations are logged for audit
        - Warning: Destructive operation if clean=true
    
    Path Parameters:
        - backup_id (str): UUID of backup to restore from (must exist)
    
    Request Body:
        RestoreRequest (JSON):
            - target_db (str, optional): Target database name (uses current if not provided)
            - clean (bool, optional): Clean database before restore (default: false)
                - If true: drops existing objects and schema before restoring
                - If false: merges restored data with existing database
    
    Returns:
        dict: Restore job status and details:
            {
                "message": "Restore started in background",
                "backup_id": <str>,
                "target_db": <str>,
                "clean": <bool>
            }
    
    Raises:
        HTTPException(400): Backup file not found on disk or invalid parameters
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Backup:edit scope
        HTTPException(404): Backup with given ID not found
        HTTPException(500): pg_restore command failed
    
    Example:
        Request:
            POST /backup/f47ac10b-58cc-4372-a567-0e02b2c3d479/restore
            Headers: Authorization: Bearer <jwt_token>
            Body:
            {
                "target_db": "gencharge_recovery",
                "clean": true
            }
        
        Response (202 Accepted):
            {
                "message": "Restore started in background",
                "backup_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "target_db": "gencharge_recovery",
                "clean": true
            }
        
        Note: Monitor logs or check backup status endpoint for restore completion.
    """
    result = await db.execute(select(Backup).where(Backup.backup_id == backup_id))
    backup = result.scalar_one_or_none()

    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    if not backup.storage_url or not os.path.exists(backup.storage_url):
        raise HTTPException(status_code=400, detail="Backup file not found on disk")
    details: dict = backup.details
    details.update({"restore_db": request.target_db})
    backup_file = backup.storage_url
    log = BackupRestoreLogCreate(
        job_type="restore",
        backup_id=backup_id,
        status="started",
        details=details,
        action_by=current_user.admin_id
    )

    # Use current DB if target_db not provided
    target_db = request.target_db or (await db.execute(select("current_database()"))).scalar()

    # Build pg_restore command
    cmd = [
        "pg_restore",
        "--verbose",
        "--format=custom",
        "--dbname", target_db,
    ]

    if request.clean:
        cmd.extend(["--clean", "--if-exists"])

    cmd.extend(["--jobs=4", backup_file])  # Parallel restore

    logger.info(f"Starting restore: {' '.join(cmd)}")

    # Run in background
    background_tasks.add_task(run_pg_restore, cmd, backup_id, db)

    await insert_backup_restore_log(mongo_db=mongo_db,log_data=log)

    return {
        "message": "Restore started in background",
        "backup_id": backup_id,
        "target_db": target_db,
        "clean": request.clean
    }


