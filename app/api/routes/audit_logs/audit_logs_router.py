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
    Retrieve audit logs with optional filtering.
    
    Fetches system audit logs documenting all administrative actions, API calls,
    data modifications, and sensitive operations. Useful for compliance, security
    investigation, and understanding system activity history. Logs are immutable
    and cannot be deleted (read-only endpoint).
    
    Security:
        - Requires valid JWT access token
        - Scope: AuditLogs:read
        - Restricted to admin/compliance team
        - All access is logged
    
    Query Parameters:
        - limit (int, optional): Max records to return (default: 50, max: 200)
        - service (str, optional): Filter by service/module (e.g., "auth", "backup", "users")
        - user_id (str, optional): Filter by user/admin who performed action
        - start_date (datetime, optional): Filter logs after this date (ISO 8601 format)
            - Example: "2024-01-01T00:00:00Z"
        - end_date (datetime, optional): Filter logs before this date (ISO 8601 format)
            - Example: "2024-01-31T23:59:59Z"
    
    Returns:
        dict: Audit log response containing:
            - count (int): Number of logs returned
            - logs (list): Array of audit log entries with:
                - _id (str): Log entry ID
                - timestamp (datetime): When action occurred
                - service (str): Service/module that performed action
                - user_id (str): User or admin who performed action
                - action (str): What action was performed
                - resource (str): What resource was affected
                - resource_id (int, optional): ID of affected resource
                - status (str): Action status (success, failed, denied)
                - details (dict): Additional context/parameters
                - ip_address (str, optional): Source IP address
                - changes (dict, optional): Data before/after changes
    
    Raises:
        HTTPException(400): Invalid date format (must be ISO 8601)
        HTTPException(401): User not authenticated
        HTTPException(403): Missing AuditLogs:read scope
    
    Example:
        Request:
            GET /audit-logs?service=backup&limit=100&start_date=2024-01-01T00:00:00Z&end_date=2024-01-31T23:59:59Z
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            {
                "count": 3,
                "logs": [
                    {
                        "_id": "507f1f77bcf86cd799439011",
                        "timestamp": "2024-01-20T14:30:00Z",
                        "service": "backup",
                        "user_id": "1",
                        "action": "create_backup",
                        "resource": "database",
                        "status": "success",
                        "details": {
                            "tables": ["users", "transactions"],
                            "size_mb": 245.67
                        }
                    },
                    {
                        "_id": "507f1f77bcf86cd799439012",
                        "timestamp": "2024-01-19T10:00:00Z",
                        "service": "users",
                        "user_id": "1",
                        "action": "block_user",
                        "resource": "user",
                        "resource_id": 123,
                        "status": "success",
                        "details": {
                            "reason": "Suspicious activity"
                        }
                    }
                ]
            }
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
