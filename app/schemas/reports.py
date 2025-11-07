from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class AdminReportFilter(BaseModel):
    roles: Optional[List[str]] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    updated_from: Optional[datetime] = None
    updated_to: Optional[datetime] = None
    order_by: Optional[Literal["name", "email", "created_at", "updated_at"]] = "created_at"
    order_dir: Optional[Literal["asc", "desc"]] = "asc"
    limit: Optional[int] = 0
    offset: Optional[int] = 0
    export_type: Optional[Literal["excel", "csv", "pdf", "none"]] = "none"


class AdminOut(BaseModel):
    admin_id: int
    name: str
    email: str
    phone_number: str
    role_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AutoPayReportFilter(BaseModel):
    # Basic filters
    statuses: Optional[List[Literal["enabled", "disabled"]]] = None
    tags: Optional[List[Literal["onetime", "regular"]]] = None

    # Relational filters
    plan_ids: Optional[List[int]] = None
    plan_types: Optional[List[Literal["prepaid", "postpaid"]]] = None
    user_ids: Optional[List[int]] = None
    phone_numbers: Optional[List[str]] = None

    # Date ranges (next_due_date, created_at)
    next_due_from: Optional[datetime] = None
    next_due_to: Optional[datetime] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None

    # Ordering & pagination
    order_by: Optional[Literal["autopay_id", "next_due_date", "created_at", "price", "plan_name"]] = "created_at"
    order_dir: Optional[Literal["asc", "desc"]] = "asc"

    # if limit==0 or offset==0 => skip pagination (as requested)
    limit: Optional[int] = Field(default=0, description="0 means no pagination")
    offset: Optional[int] = Field(default=0, description="0 means no pagination")

    # export options
    export_type: Optional[Literal["none", "csv", "excel", "pdf"]] = "none"


class AutoPayOut(BaseModel):
    autopay_id: int
    user_id: int
    plan_id: int
    status: str
    tag: str
    phone_number: str
    next_due_date: Optional[datetime]
    created_at: Optional[datetime]

    # Denormalized/related fields for convenience
    plan_name: Optional[str] = None
    plan_price: Optional[int] = None
    plan_type: Optional[str] = None
    user_name: Optional[str] = None
    user_phone: Optional[str] = None

    class Config:
        from_attributes = True


class BackupReportFilter(BaseModel):
    backup_data: Optional[List[str]] = None  # product / orders / users
    backup_status: Optional[List[Literal["failed", "success"]]] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    min_size_mb: Optional[float] = None
    max_size_mb: Optional[float] = None
    created_by: Optional[List[int]] = None

    order_by: Optional[Literal["created_at", "size_mb", "backup_status", "backup_data", "snapshot_name"]] = "created_at"
    order_dir: Optional[Literal["asc", "desc"]] = "desc"

    limit: Optional[int] = Field(default=0, description="0 means no pagination")
    offset: Optional[int] = Field(default=0, description="0 means no pagination")

    export_type: Optional[Literal["none", "csv", "excel", "pdf"]] = "none"


class BackupOut(BaseModel):
    backup_id: str
    backup_data: str
    snapshot_name: str
    storage_url: Optional[str]
    backup_status: str
    size_mb: Optional[str]
    description: Optional[str]
    details: Optional[dict]
    created_at: datetime
    created_by: Optional[int]

    class Config:
        from_attributes = True


class CurrentActivePlansFilter(BaseModel):
    # direct filters
    ids: Optional[List[int]] = None
    user_ids: Optional[List[int]] = None
    plan_ids: Optional[List[int]] = None
    phone_numbers: Optional[List[str]] = None
    statuses: Optional[List[str]] = None  # e.g., ["active", "expired"] depending on CurrentPlanStatus
    plan_types: Optional[List[Literal["prepaid", "postpaid"]]] = None
    plan_statuses: Optional[List[Literal["active", "inactive"]]] = None

    # validity & date ranges
    valid_from_from: Optional[datetime] = None
    valid_from_to: Optional[datetime] = None
    valid_to_from: Optional[datetime] = None
    valid_to_to: Optional[datetime] = None

    # Ordering & pagination
    order_by: Optional[Literal[
        "id", "user_id", "plan_id", "phone_number", "valid_from", "valid_to", "status",
        "plan_name", "plan_price", "user_name"
    ]] = "valid_to"
    order_dir: Optional[Literal["asc", "desc"]] = "asc"

    # Pagination: if limit==0 OR offset==0 -> skip pagination
    limit: Optional[int] = Field(default=0, description="0 means no pagination")
    offset: Optional[int] = Field(default=0, description="0 means no pagination")

    # export options
    export_type: Optional[Literal["none", "csv", "excel", "pdf"]] = "none"


class CurrentActivePlanOut(BaseModel):
    id: int
    user_id: int
    plan_id: int
    phone_number: str
    valid_from: datetime
    valid_to: datetime
    status: str

    # denormalized fields
    plan_name: Optional[str] = None
    plan_price: Optional[int] = None
    plan_type: Optional[str] = None
    user_name: Optional[str] = None
    user_phone: Optional[str] = None

    class Config:
        from_attributes = True
