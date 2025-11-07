# routers/backup.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from ....models.backup import Backup
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from ....dependencies.auth import get_current_user
from ....schemas.backup import BackupRequest, BackupResponse, BackupCreateResponse, RestoreRequest
from ....models.admins import Admin
from ....services.backup import perform_pg_dump_backup_async, run_pg_restore
from ....core.database import get_db
import asyncio
import datetime
import shutil
import os 
import logging
from ....crud.backup import create_backup_record

router = APIRouter(prefix="/backup", tags=["Backup"])
logger = logging.getLogger(__name__)

@router.post("/create", response_model=BackupCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_backup(
    request: BackupRequest,
    db = Depends(get_db),
    current_user: Admin = Depends(get_current_user)
):
    """
    Perform pg_dump backup for specified tables with optional date range filtering.
    
    - Accepts list of tables with optional `date_column`, `start_date`, `end_date`
    - Uses existing `get_db()` session
    - Returns backup file info on success
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

    try:
        result = await perform_pg_dump_backup_async(
            table_date_ranges=table_date_ranges,
            db_session=db
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Backup failed. Check server logs or pg_dump permissions."
            )
        await create_backup_record(
            db=db,
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
async def list_backups(db: AsyncSession = Depends(get_db)):
    """
    Retrieve all backup records from the database.
    """
    result = await db.execute(select(Backup).order_by(Backup.created_at.desc()))
    backups = result.scalars().all()
    return backups


# 2. DELETE BACKUP BY ID
@router.delete("/{backup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup(
    backup_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete backup record from DB and optionally remove the file.
    """
    result = await db.execute(select(Backup).where(Backup.backup_id == backup_id))
    backup = result.scalar_one_or_none()

    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    # Optional: Delete physical file in background
    if backup.storage_url and os.path.exists(backup.storage_url):
        background_tasks.add_task(shutil.rmtree if os.path.isdir(backup.storage_url) else os.remove, backup.storage_url)

    # Delete from DB
    await db.execute(delete(Backup).where(Backup.backup_id == backup_id))
    await db.commit()
    return None


# 3. RESTORE BACKUP BY ID
@router.post("/{backup_id}/restore", status_code=status.HTTP_202_ACCEPTED)
async def restore_backup(
    backup_id: str,
    request: RestoreRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Restore backup using `pg_restore`. Runs in background.
    """
    result = await db.execute(select(Backup).where(Backup.backup_id == backup_id))
    backup = result.scalar_one_or_none()

    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    if not backup.storage_url or not os.path.exists(backup.storage_url):
        raise HTTPException(status_code=400, detail="Backup file not found on disk")

    backup_file = backup.storage_url

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

    return {
        "message": "Restore started in background",
        "backup_id": backup_id,
        "target_db": target_db,
        "clean": request.clean
    }


