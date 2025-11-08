# app/audit/routes.py
from fastapi import APIRouter, Depends, Query, Security
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from datetime import datetime
from ....core.document_db import get_mongo_db
from ....models.admins import Admin
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes


router = APIRouter()

@router.get("/audit-logs")
async def get_audit_logs(
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    limit: int = Query(50, le=200),
    current_user: Admin = Depends(get_current_user),
    auth = Security(Depends(require_scopes), scopes=["AuditLogs:read"]),
    service: str | None = None,
    user_id: str | None = None,
    start_date: Optional[str] = Query(None, description="Start date in ISO format (e.g. 2025-11-01T00:00:00Z)"),
    end_date: Optional[str] = Query(None, description="End date in ISO format (e.g. 2025-11-08T23:59:59Z)"),
):
    """
    Retrieve audit logs (read-only).
    Supports optional filtering by service and user_id.
    """
    audit_collection = db["audit_logs"]

    query = {}
    if service:
        query["service"] = service
    if user_id:
        query["user_id"] = user_id

    # Handle date range filtering
    if start_date or end_date:
        query["timestamp"] = {}
        if start_date:
            try:
                query["timestamp"]["$gte"] = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            except ValueError:
                return {"error": "Invalid start_date format. Use ISO 8601 (e.g., 2025-11-01T00:00:00Z)"}
        if end_date:
            try:
                query["timestamp"]["$lte"] = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except ValueError:
                return {"error": "Invalid end_date format. Use ISO 8601 (e.g., 2025-11-08T23:59:59Z)"}

    cursor = (
        audit_collection
        .find(query)
        .sort("timestamp", -1)
        .limit(limit)
    )

    logs = await cursor.to_list(length=limit)
    for log in logs:
        log["_id"] = str(log["_id"])  # Convert ObjectId to string

    return {"count": len(logs), "logs": logs}
