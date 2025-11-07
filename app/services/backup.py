# core/backup.py
import os
import asyncio
import subprocess
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import text, select, update, delete
from ..models.backup import Backup
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from ..core.config import settings

env = os.environ.copy()
env["PGPASSWORD"] = settings.POSTGRES_PASSWORD
from fastapi import Depends
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import your existing get_db function

async def perform_pg_dump_backup_async(
    db_session: AsyncSession,
    table_date_ranges: List[Dict[str, Optional[str]]],
    backup_dir: str = "backups",
) -> Optional[Dict[str, str]]:
    """
    Perform pg_dump backup asynchronously using an **existing AsyncSession** from get_db().
    
    Args:
        backup_dir (str): Directory to store backup files
        table_date_ranges (List[Dict]): List of tables with optional date filtering
        db_session: Async generator yielding AsyncSession (from get_db())

    Returns:
        Dict with backup_file, backup_path, size_mb or None on failure
    """
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.sql"
    backup_filepath = os.path.join(backup_dir, backup_filename)

    session = None  # Will be set inside context
    try:
        # Use the injected async session (from get_db())
        async with db_session as session:
            # Extract database name from session for pg_dump
            db_name_result = await session.execute(text("SELECT current_database();"))
            db_name = db_name_result.scalar_one()

            # Build base pg_dump command
            pg_dump_cmd = [
                "pg_dump",
                "--format=custom",
                "--compress=gzip",
                "--file", backup_filepath,
                db_name
            ]

            # Validate tables and build --table / --where clauses
            for item in table_date_ranges:
                table_name = item["table_name"]
                date_column = item.get("date_column")
                start_date = item.get("start_date")
                end_date = item.get("end_date")

                # Check if table exists
                result = await session.execute(text(
                    f"SELECT to_regclass('public.{table_name}');"
                ))
                table_exists = result.scalar()

                if not table_exists:
                    logger.warning(f"Table {table_name} does not exist. Skipping.")
                    continue

                if date_column and start_date and end_date:
                    # Validate column exists
                    col_result = await session.execute(text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = :tbl AND column_name = :col"
                    ), {"tbl": table_name, "col": date_column})
                    col_exists = col_result.fetchone()

                    if not col_exists:
                        logger.warning(f"Column {date_column} not found in {table_name}. Dumping full table.")
                    else:
                        where_clause = f"{date_column} >= '{start_date}' AND {date_column} <= '{end_date}'"
                        pg_dump_cmd.extend(["--table", table_name, "--where", where_clause])
                else:
                    pg_dump_cmd.extend(["--table", table_name])

            # No need to commit — we're only reading

        # Add compression (outside session context)
        pg_dump_cmd.insert(1, "--compress=gzip")

        logger.info(f"Starting backup to {backup_filepath}")
        logger.info(f"Command: {' '.join(pg_dump_cmd)}")

        # Run pg_dump asynchronously
        process = await asyncio.create_subprocess_exec(
            *pg_dump_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"pg_dump failed (code {process.returncode}): {stderr.decode()}")
            return None

        # Return backup metadata
        if os.path.exists(backup_filepath):
            size_mb = round(os.path.getsize(backup_filepath) / (1024 * 1024), 2)
            backup_info = {
                "backup_file": backup_filename,
                "backup_path": backup_filepath,
                "size_mb": str(size_mb)
            }
            logger.info(f"Backup successful: {backup_info}")
            return backup_info
        else:
            logger.error("Backup file was not created.")
            return None

    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        return None


# Background task to run pg_restore
async def run_pg_restore(cmd: list, backup_id: str, db: AsyncSession):
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            # Update status to success
            await db.execute(
                update(Backup)
                .where(Backup.backup_id == backup_id)
                .values(backup_status="restored")
            )
            await db.commit()
            logger.info(f"Restore successful for {backup_id}")
        else:
            error = stderr.decode()
            logger.error(f"Restore failed for {backup_id}: {error}")
            await db.execute(
                update(Backup)
                .where(Backup.backup_id == backup_id)
                .values(backup_status="restore_failed", details={"error": error})
            )
            await db.commit()
    except Exception as e:
        logger.error(f"Restore exception for {backup_id}: {str(e)}")
        await db.execute(
            update(Backup)
            .where(Backup.backup_id == backup_id)
            .values(backup_status="restore_failed", details={"error": str(e)})
        )
        await db.commit()