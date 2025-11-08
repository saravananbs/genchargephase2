from fastapi import Depends
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..core.document_db import get_mongo_db

async def insert_audit_log(
    db: AsyncIOMotorDatabase,
    action: str,
    service: str,
    user_id: str,
    status: str = "success",
):
    """
    Insert a new audit log entry (no updates or deletes allowed).
    """
    audit_collection = db["audit_logs"]
    
    log_entry = {
        "action": action,
        "service": service,
        "user_id": user_id,
        "status": status,
        "timestamp": datetime.now(),
    }

    await audit_collection.insert_one(log_entry)
