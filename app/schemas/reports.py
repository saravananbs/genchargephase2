from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from decimal import Decimal
from uuid import UUID


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
    statuses: Optional[List[Literal["active", "expired"]]] = None  # e.g., ["active", "expired"] depending on CurrentPlanStatus
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


class OfferReportFilter(BaseModel):
    # Basic filters
    offer_ids: Optional[List[int]] = None
    offer_names: Optional[List[str]] = None
    is_special: Optional[bool] = None
    offer_type_ids: Optional[List[int]] = None
    offer_type_names: Optional[List[str]] = None
    statuses: Optional[List[Literal["active", "inactive"]]] = None
    created_by: Optional[List[int]] = None

    # date range
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None

    # ordering & pagination
    order_by: Optional[Literal[
        "offer_id", "offer_name", "offer_validity", "is_special", "created_at", "status", "offer_type_name", "created_by", "price"
    ]] = "created_at"
    order_dir: Optional[Literal["asc", "desc"]] = "desc"

    # Pagination: if limit==0 OR offset==0 -> skip pagination
    limit: Optional[int] = Field(default=0, description="0 means no pagination")
    offset: Optional[int] = Field(default=0, description="0 means no pagination")

    # export options
    export_type: Optional[Literal["none", "csv", "excel", "pdf"]] = "none"


class OfferOut(BaseModel):
    offer_id: int
    offer_name: str
    offer_validity: Optional[int]
    is_special: bool
    criteria: Optional[dict]
    description: Optional[str]
    created_at: Optional[datetime]
    created_by: Optional[int]
    status: str

    # denormalized fields
    offer_type_id: Optional[int] = None
    offer_type_name: Optional[str] = None

    class Config:
        from_attributes = True


class PlanReportFilter(BaseModel):
    plan_ids: Optional[List[int]] = None
    plan_names: Optional[List[str]] = None
    name_search: Optional[str] = None  # case-insensitive partial search
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_validity: Optional[float] = None
    max_validity: Optional[float] = None
    plan_types: Optional[List[Literal["prepaid", "postpaid"]]] = None
    plan_statuses: Optional[List[Literal["active", "inactive"]]] = None
    group_ids: Optional[List[int]] = None
    group_names: Optional[List[str]] = None
    most_popular: Optional[bool] = None
    created_by: Optional[List[int]] = None

    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None

    # ordering & pagination
    order_by: Optional[Literal[
        "plan_id", "plan_name", "price", "validity", "most_popular", "created_at", "plan_type", "status", "group_name"
    ]] = "created_at"
    order_dir: Optional[Literal["asc", "desc"]] = "desc"

    # Pagination: if limit==0 OR offset==0 => skip pagination
    limit: Optional[int] = Field(default=0, description="0 means no pagination")
    offset: Optional[int] = Field(default=0, description="0 means no pagination")

    export_type: Optional[Literal["none", "csv", "excel", "pdf"]] = "none"


class PlanOut(BaseModel):
    plan_id: int
    plan_name: str
    validity: Optional[int]
    most_popular: bool
    plan_type: str
    group_id: Optional[int]
    group_name: Optional[str]
    description: Optional[dict]  # or str depending on your criteria/description usage
    criteria: Optional[dict]
    created_at: Optional[datetime]
    created_by: Optional[int]
    price: int
    status: str

    class Config:
        from_attributes = True


class ReferralReportFilter(BaseModel):
    reward_ids: Optional[List[int]] = None
    referrer_ids: Optional[List[int]] = None
    referred_ids: Optional[List[int]] = None
    referrer_phones: Optional[List[str]] = None
    referred_phones: Optional[List[str]] = None
    statuses: Optional[List[Literal["pending", "earned"]]] = None

    # reward amount range
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None

    # date ranges
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    claimed_from: Optional[datetime] = None
    claimed_to: Optional[datetime] = None

    # ordering & pagination
    order_by: Optional[Literal[
        "reward_id", "reward_amount", "status", "created_at", "claimed_at", "referrer_name", "referred_name"
    ]] = "created_at"
    order_dir: Optional[Literal["asc", "desc"]] = "desc"

    # Pagination: if limit==0 OR offset==0 -> skip pagination
    limit: Optional[int] = Field(default=0, description="0 means no pagination")
    offset: Optional[int] = Field(default=0, description="0 means no pagination")

    export_type: Optional[Literal["none", "csv", "excel", "pdf"]] = "none"


class ReferralOut(BaseModel):
    reward_id: int
    referrer_id: int
    referred_id: int
    reward_amount: Decimal
    status: str
    created_at: datetime
    claimed_at: Optional[datetime]

    # denormalized related fields
    referrer_name: Optional[str] = None
    referrer_phone: Optional[str] = None
    referred_name: Optional[str] = None
    referred_phone: Optional[str] = None

    class Config:
        from_attributes = True


class RolePermissionReportFilter(BaseModel):
    role_permission_ids: Optional[List[int]] = None
    role_ids: Optional[List[int]] = None
    permission_ids: Optional[List[int]] = None
    role_names: Optional[List[str]] = None
    resources: Optional[List[str]] = None
    read: Optional[bool] = None
    write: Optional[bool] = None
    edit: Optional[bool] = None
    delete: Optional[bool] = None

    order_by: Optional[Literal[
        "id", "role_id", "permission_id", "role_name", "resource", "read", "write", "edit", "delete"
    ]] = "role_id"
    order_dir: Optional[Literal["asc", "desc"]] = "asc"

    limit: Optional[int] = Field(default=0, description="0 means no pagination")
    offset: Optional[int] = Field(default=0, description="0 means no pagination")

    export_type: Optional[Literal["none", "csv", "excel", "pdf"]] = "none"


class RolePermissionOut(BaseModel):
    id: int
    role_id: int
    permission_id: int
    role_name: Optional[str] = None
    resource: Optional[str] = None
    read: bool
    write: bool
    edit: bool
    delete: bool

    class Config:
        from_attributes = True


class SessionsReportFilter(BaseModel):
    # Basic filters
    session_ids: Optional[List[UUID]] = None   # UUIDs as strings
    user_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None

    # Token / JTI filters
    jtis: Optional[List[UUID]] = None
    refresh_tokens_contains: Optional[str] = None  # substring search

    # Datetime ranges (timezone-aware allowed; we will normalize)
    refresh_expires_from: Optional[datetime] = None
    refresh_expires_to: Optional[datetime] = None
    login_time_from: Optional[datetime] = None
    login_time_to: Optional[datetime] = None
    last_active_from: Optional[datetime] = None
    last_active_to: Optional[datetime] = None
    revoked_from: Optional[datetime] = None
    revoked_to: Optional[datetime] = None

    # Ordering & pagination
    order_by: Optional[Literal[
        "session_id", "user_id", "refresh_token_expires_at", "login_time",
        "last_active", "is_active", "revoked_at"
    ]] = "last_active"
    order_dir: Optional[Literal["asc", "desc"]] = "desc"

    # If limit==0 OR offset==0 => skip pagination (return all matching rows / export all)
    limit: Optional[int] = Field(default=0, description="0 means no pagination")
    offset: Optional[int] = Field(default=0, description="0 means no pagination")

    export_type: Optional[Literal["none", "csv", "excel", "pdf"]] = "none"


class SessionOut(BaseModel):
    session_id: str
    user_id: Optional[int]
    refresh_token: str
    jti: str
    refresh_token_expires_at: Optional[datetime]
    login_time: Optional[datetime]
    last_active: Optional[datetime]
    is_active: bool
    revoked_at: Optional[datetime]

    class Config:
        from_attributes = True


class TransactionsReportFilter(BaseModel):
    txn_ids: Optional[List[int]] = None
    user_ids: Optional[List[int]] = None

    categories: Optional[List[Literal["wallet", "service"]]] = None
    txn_types: Optional[List[Literal["credit", "debit"]]] = None

    min_amount: Optional[float] = None
    max_amount: Optional[float] = None

    service_types: Optional[List[Literal["prepaid", "postpaid"]]] = None
    plan_ids: Optional[List[int]] = None
    offer_ids: Optional[List[int]] = None

    from_phone_numbers: Optional[List[str]] = None
    to_phone_numbers: Optional[List[str]] = None

    sources: Optional[List[Literal["recharge", "wallet_topup", "refund", "referral_reward", "autopay"]]] = None
    statuses: Optional[List[Literal["success", "failed", "pending"]]] = None
    payment_methods: Optional[List[Literal["UPI", "Card", "NetBanking", "Wallet"]]] = None
    payment_transaction_id_contains: Optional[str] = None

    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None

    # ordering & pagination
    order_by: Optional[Literal[
        "txn_id", "user_id", "amount", "created_at", "category", "txn_type", "service_type", "source", "status", "payment_method"
    ]] = "created_at"
    order_dir: Optional[Literal["asc", "desc"]] = "desc"

    # If limit==0 OR offset==0 => skip pagination
    limit: Optional[int] = Field(default=0, description="0 means no pagination")
    offset: Optional[int] = Field(default=0, description="0 means no pagination")

    export_type: Optional[Literal["none", "csv", "excel", "pdf"]] = "none"


class TransactionOut(BaseModel):
    txn_id: int
    user_id: Optional[int]
    category: str
    txn_type: str
    amount: Decimal
    service_type: Optional[str]
    plan_id: Optional[int]
    offer_id: Optional[int]
    from_phone_number: Optional[str]
    to_phone_number: Optional[str]
    source: str
    status: str
    payment_method: Optional[str]
    payment_transaction_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UsersArchiveFilter(BaseModel):
    user_ids: Optional[List[int]] = None
    name_search: Optional[str] = None    # partial case-insensitive search
    emails: Optional[List[str]] = None
    phone_numbers: Optional[List[str]] = None

    user_types: Optional[List[Literal["prepaid", "postpaid"]]] = None
    statuses: Optional[List[Literal["active", "blocked"]]] = None

    min_wallet: Optional[float] = None
    max_wallet: Optional[float] = None

    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    deleted_from: Optional[datetime] = None
    deleted_to: Optional[datetime] = None

    order_by: Optional[Literal[
        "user_id", "name", "email", "phone_number", "user_type", "status",
        "wallet_balance", "created_at", "deleted_at"
    ]] = "deleted_at"
    order_dir: Optional[Literal["asc", "desc"]] = "desc"

    # Pagination: apply only when BOTH limit>0 AND offset>0
    limit: Optional[int] = Field(default=0, description="0 means no pagination")
    offset: Optional[int] = Field(default=0, description="0 means no pagination")

    export_type: Optional[Literal["none", "csv", "excel", "pdf"]] = "none"


class UserArchiveOut(BaseModel):
    user_id: int
    name: Optional[str]
    email: Optional[str]
    phone_number: Optional[str]
    referral_code: Optional[str]
    referee_code: Optional[str]
    user_type: Optional[str]
    status: Optional[str]
    wallet_balance: Optional[Decimal]
    created_at: Optional[datetime]
    deleted_at: Optional[datetime]

    class Config:
        from_attributes = True


class UsersReportFilter(BaseModel):
    user_ids: Optional[List[int]] = None
    name_search: Optional[str] = None        # case-insensitive partial match on name
    emails: Optional[List[str]] = None
    phone_numbers: Optional[List[str]] = None

    user_types: Optional[List[Literal["prepaid", "postpaid"]]] = None
    statuses: Optional[List[Literal["active", "blocked", "deactive"]]] = None

    min_wallet: Optional[float] = None
    max_wallet: Optional[float] = None

    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    updated_from: Optional[datetime] = None
    updated_to: Optional[datetime] = None

    # ordering & pagination
    order_by: Optional[Literal[
        "user_id","name","email","phone_number","user_type","status","wallet_balance","created_at","updated_at"
    ]] = "created_at"
    order_dir: Optional[Literal["asc","desc"]] = "desc"

    # Pagination: if limit==0 OR offset==0 => skip pagination (apply only when both > 0)
    limit: Optional[int] = Field(default=0, description="0 means no pagination")
    offset: Optional[int] = Field(default=0, description="0 means no pagination")

    export_type: Optional[Literal["none","csv","excel","pdf"]] = "none"


class UserOut(BaseModel):
    user_id: int
    name: Optional[str]
    email: Optional[str]
    phone_number: Optional[str]
    referral_code: Optional[str]
    referee_code: Optional[str]
    user_type: Optional[str]
    status: Optional[str]
    wallet_balance: Optional[Decimal]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True