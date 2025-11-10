from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from decimal import Decimal
from uuid import UUID
from dataclasses import dataclass
from fastapi import Query


@dataclass
class AdminReportFilter:
    roles: Optional[List[str]] = Query(
        default=None,
        description="List of roles to filter by"
    )
    created_from: Optional[datetime] = Query(
        default=None,
        description="Filter users created after this datetime (ISO format)"
    )
    created_to: Optional[datetime] = Query(
        default=None,
        description="Filter users created before this datetime (ISO format)"
    )
    updated_from: Optional[datetime] = Query(
        default=None,
        description="Filter users updated after this datetime (ISO format)"
    )
    updated_to: Optional[datetime] = Query(
        default=None,
        description="Filter users updated before this datetime (ISO format)"
    )
    order_by: Literal["name", "email", "created_at", "updated_at"] = Query(
        default="created_at",
        description="Field to sort by"
    )
    order_dir: Literal["asc", "desc"] = Query(
        default="asc",
        description="Sort direction: ascending or descending"
    )
    limit: int = Query(
        default=0,
        ge=0,
        description="Number of records to limit"
    )
    offset: int = Query(
        default=0,
        ge=0,
        description="Offset for pagination"
    )
    export_type: Literal["excel", "csv", "pdf", "none"] = Query(
        default="none",
        description="Export file type"
    )


class AdminOut(BaseModel):
    """Complete admin information for report responses.
    
    Attributes:
        admin_id (int): Unique admin identifier.
        name (str): Admin's full name.
        email (str): Admin's email address.
        phone_number (str): Admin's phone number.
        role_name (str): Role name assigned to this admin.
        created_at (datetime): When the admin account was created.
        updated_at (datetime): When the admin account was last updated.
    """
    admin_id: int
    name: str
    email: str
    phone_number: str
    role_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@dataclass
class AutoPayReportFilter:
    # Basic filters
    statuses: Optional[List[Literal["enabled", "disabled"]]] = Query(
        default=None,
        description="Filter by autopay status (enabled or disabled)"
    )
    tags: Optional[List[Literal["onetime", "regular"]]] = Query(
        default=None,
        description="Filter by autopay tag type (onetime or regular)"
    )

    # Relational filters
    plan_ids: Optional[List[int]] = Query(
        default=None,
        description="Filter by one or more plan IDs"
    )
    plan_types: Optional[List[Literal["prepaid", "postpaid"]]] = Query(
        default=None,
        description="Filter by plan type (prepaid or postpaid)"
    )
    user_ids: Optional[List[int]] = Query(
        default=None,
        description="Filter by one or more user IDs"
    )
    phone_numbers: Optional[List[str]] = Query(
        default=None,
        description="Filter by one or more phone numbers"
    )

    # Date ranges
    next_due_from: Optional[datetime] = Query(
        default=None,
        description="Filter by next due date (from)"
    )
    next_due_to: Optional[datetime] = Query(
        default=None,
        description="Filter by next due date (to)"
    )
    created_from: Optional[datetime] = Query(
        default=None,
        description="Filter by creation date (from)"
    )
    created_to: Optional[datetime] = Query(
        default=None,
        description="Filter by creation date (to)"
    )

    # Ordering & pagination
    order_by: Literal["autopay_id", "next_due_date", "created_at", "price", "plan_name"] = Query(
        default="created_at",
        description="Field to order results by"
    )
    order_dir: Literal["asc", "desc"] = Query(
        default="asc",
        description="Order direction: asc or desc"
    )
    limit: int = Query(
        default=0,
        ge=0,
        description="0 means no pagination"
    )
    offset: int = Query(
        default=0,
        ge=0,
        description="0 means no pagination"
    )

    # Export options
    export_type: Literal["none", "csv", "excel", "pdf"] = Query(
        default="none",
        description="Export type for report generation"
    )


class AutoPayOut(BaseModel):
    """Complete autopay subscription information for report responses.
    
    Attributes:
        autopay_id (int): Unique autopay subscription ID.
        user_id (int): ID of the user who owns this autopay.
        plan_id (int): ID of the plan in autopay.
        status (str): Status (enabled/disabled).
        tag (str): Tag type (onetime/regular).
        phone_number (str): Associated phone number.
        next_due_date (Optional[datetime]): Next scheduled payment date.
        created_at (Optional[datetime]): When autopay was created.
        plan_name (Optional[str]): Denormalized plan name for convenience.
        plan_price (Optional[int]): Denormalized plan price.
        plan_type (Optional[str]): Denormalized plan type (prepaid/postpaid).
        user_name (Optional[str]): Denormalized user name.
        user_phone (Optional[str]): Denormalized user phone number.
    """
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


@dataclass
class BackupReportFilter:
    # Basic filters
    backup_data: Optional[List[str]] = Query(
        default=None,
        description="Filter by backup data type (e.g., product, orders, users)"
    )
    backup_status: Optional[List[Literal["failed", "success"]]] = Query(
        default=None,
        description="Filter by backup status (failed or success)"
    )

    # Date range filters
    created_from: Optional[datetime] = Query(
        default=None,
        description="Filter backups created after this datetime (ISO format)"
    )
    created_to: Optional[datetime] = Query(
        default=None,
        description="Filter backups created before this datetime (ISO format)"
    )

    # Size filters
    min_size_mb: Optional[float] = Query(
        default=None,
        ge=0,
        description="Minimum backup size in MB"
    )
    max_size_mb: Optional[float] = Query(
        default=None,
        ge=0,
        description="Maximum backup size in MB"
    )

    # Relational filters
    created_by: Optional[List[int]] = Query(
        default=None,
        description="Filter backups created by specific user IDs"
    )

    # Sorting
    order_by: Literal[
        "created_at", "size_mb", "backup_status", "backup_data", "snapshot_name"
    ] = Query(
        default="created_at",
        description="Field to order results by"
    )
    order_dir: Literal["asc", "desc"] = Query(
        default="desc",
        description="Order direction: asc or desc"
    )

    # Pagination
    limit: int = Query(
        default=0,
        ge=0,
        description="Limit number of records (0 means no pagination)"
    )
    offset: int = Query(
        default=0,
        ge=0,
        description="Offset for pagination (0 means no pagination)"
    )

    # Export options
    export_type: Literal["none", "csv", "excel", "pdf"] = Query(
        default="none",
        description="Export type for report (none, csv, excel, or pdf)"
    )


class BackupOut(BaseModel):
    """Complete backup record information for report responses.
    
    Attributes:
        backup_id (str): Unique backup identifier.
        backup_data (str): Serialized backup data.
        snapshot_name (str): Name of the backup snapshot.
        storage_url (Optional[str]): URL/path where backup is stored.
        backup_status (str): Status of the backup (success/failed/partial).
        size_mb (Optional[str]): Size of backup in megabytes.
        description (Optional[str]): Description of the backup.
        details (Optional[dict]): Additional backup metadata.
        created_at (datetime): When backup was created.
        created_by (Optional[int]): User ID who initiated the backup.
    """
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


@dataclass
class CurrentActivePlansFilter:
    # Direct filters
    ids: Optional[List[int]] = Query(
        default=None,
        description="Filter by plan record IDs"
    )
    user_ids: Optional[List[int]] = Query(
        default=None,
        description="Filter by user IDs"
    )
    plan_ids: Optional[List[int]] = Query(
        default=None,
        description="Filter by plan IDs"
    )
    phone_numbers: Optional[List[str]] = Query(
        default=None,
        description="Filter by phone numbers"
    )
    statuses: Optional[List[Literal["active", "expired"]]] = Query(
        default=None,
        description="Filter by plan status (active, expired)"
    )
    plan_types: Optional[List[Literal["prepaid", "postpaid"]]] = Query(
        default=None,
        description="Filter by plan type (prepaid or postpaid)"
    )
    plan_statuses: Optional[List[Literal["active", "inactive"]]] = Query(
        default=None,
        description="Filter by plan activity status (active or inactive)"
    )

    # Validity & date ranges
    valid_from_from: Optional[datetime] = Query(
        default=None,
        description="Filter for valid_from >= this datetime (ISO format)"
    )
    valid_from_to: Optional[datetime] = Query(
        default=None,
        description="Filter for valid_from <= this datetime (ISO format)"
    )
    valid_to_from: Optional[datetime] = Query(
        default=None,
        description="Filter for valid_to >= this datetime (ISO format)"
    )
    valid_to_to: Optional[datetime] = Query(
        default=None,
        description="Filter for valid_to <= this datetime (ISO format)"
    )

    # Ordering & pagination
    order_by: Literal[
        "id", "user_id", "plan_id", "phone_number",
        "valid_from", "valid_to", "status",
        "plan_name", "plan_price", "user_name"
    ] = Query(
        default="valid_to",
        description="Field to order the results by"
    )
    order_dir: Literal["asc", "desc"] = Query(
        default="asc",
        description="Order direction (asc or desc)"
    )

    # Pagination
    limit: int = Query(
        default=0,
        ge=0,
        description="Number of records to fetch (0 means no pagination)"
    )
    offset: int = Query(
        default=0,
        ge=0,
        description="Pagination offset (0 means no pagination)"
    )

    # Export options
    export_type: Literal["none", "csv", "excel", "pdf"] = Query(
        default="none",
        description="Export type for the report (none, csv, excel, pdf)"
    )


class CurrentActivePlanOut(BaseModel):
    """Current active plan subscription information for report responses.
    
    Attributes:
        id (int): Unique subscription record ID.
        user_id (int): ID of the user who owns this plan.
        plan_id (int): ID of the subscribed plan.
        phone_number (str): Associated phone number.
        valid_from (datetime): When the plan becomes active.
        valid_to (datetime): When the plan expires.
        status (str): Current subscription status.
        plan_name (Optional[str]): Denormalized plan name.
        plan_price (Optional[int]): Denormalized plan price.
        plan_type (Optional[str]): Denormalized plan type (prepaid/postpaid).
        user_name (Optional[str]): Denormalized user name.
        user_phone (Optional[str]): Denormalized user phone number.
    """
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


@dataclass
class OfferReportFilter:
    # Basic filters
    offer_ids: Optional[List[int]] = Query(
        default=None,
        description="Filter by one or more offer IDs"
    )
    offer_names: Optional[List[str]] = Query(
        default=None,
        description="Filter by one or more offer names"
    )
    is_special: Optional[bool] = Query(
        default=None,
        description="Filter by whether the offer is special (true/false)"
    )
    offer_type_ids: Optional[List[int]] = Query(
        default=None,
        description="Filter by one or more offer type IDs"
    )
    offer_type_names: Optional[List[str]] = Query(
        default=None,
        description="Filter by one or more offer type names"
    )
    statuses: Optional[List[Literal["active", "inactive"]]] = Query(
        default=None,
        description="Filter by offer status (active/inactive)"
    )
    created_by: Optional[List[int]] = Query(
        default=None,
        description="Filter by IDs of creators"
    )

    # Date range
    created_from: Optional[datetime] = Query(
        default=None,
        description="Filter offers created after this datetime (ISO format)"
    )
    created_to: Optional[datetime] = Query(
        default=None,
        description="Filter offers created before this datetime (ISO format)"
    )

    # Ordering
    order_by: Literal[
        "offer_id", "offer_name", "offer_validity", "is_special",
        "created_at", "status", "offer_type_name", "created_by", "price"
    ] = Query(
        default="created_at",
        description="Field to order results by"
    )
    order_dir: Literal["asc", "desc"] = Query(
        default="desc",
        description="Order direction (asc or desc)"
    )

    # Pagination
    limit: int = Query(
        default=0,
        ge=0,
        description="Number of records to limit (0 means no pagination)"
    )
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of records to skip (0 means no pagination)"
    )

    # Export options
    export_type: Literal["none", "csv", "excel", "pdf"] = Query(
        default="none",
        description="Export type for the report (none, csv, excel, pdf)"
    )


class OfferOut(BaseModel):
    """Complete offer information for report responses.
    
    Attributes:
        offer_id (int): Unique offer identifier.
        offer_name (str): Name of the offer.
        offer_validity (Optional[int]): Validity period in days.
        is_special (bool): Whether this is a special/featured offer.
        criteria (Optional[dict]): Eligibility criteria for the offer.
        description (Optional[str]): Description of the offer.
        created_at (Optional[datetime]): When offer was created.
        created_by (Optional[int]): User ID who created the offer.
        status (str): Status (active/inactive).
        offer_type_name (Optional[str]): Denormalized offer type name.
    """
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


@dataclass
class PlanReportFilter:
    plan_ids: Optional[List[int]] = Query(None, description="Filter by plan IDs")
    plan_names: Optional[List[str]] = Query(None, description="Filter by plan names")
    name_search: Optional[str] = Query(None, description="Case-insensitive partial plan name search")
    min_price: Optional[float] = Query(None, ge=0, description="Minimum plan price")
    max_price: Optional[float] = Query(None, ge=0, description="Maximum plan price")
    min_validity: Optional[float] = Query(None, ge=0, description="Minimum validity in days")
    max_validity: Optional[float] = Query(None, ge=0, description="Maximum validity in days")
    plan_types: Optional[List[Literal["prepaid", "postpaid"]]] = Query(None, description="Filter by plan type")
    plan_statuses: Optional[List[Literal["active", "inactive"]]] = Query(None, description="Filter by plan status")
    group_ids: Optional[List[int]] = Query(None, description="Filter by plan group IDs")
    group_names: Optional[List[str]] = Query(None, description="Filter by plan group names")
    most_popular: Optional[bool] = Query(None, description="Filter by most popular plans")
    created_by: Optional[List[int]] = Query(None, description="Filter by creator user IDs")
    created_from: Optional[datetime] = Query(None, description="Created after this datetime")
    created_to: Optional[datetime] = Query(None, description="Created before this datetime")

    order_by: Literal["plan_id", "plan_name", "price", "validity", "most_popular", "created_at", "plan_type", "status", "group_name"] = Query("created_at")
    order_dir: Literal["asc", "desc"] = Query("desc")
    limit: int = Query(0, ge=0, description="0 means no pagination")
    offset: int = Query(0, ge=0, description="0 means no pagination")
    export_type: Literal["none", "csv", "excel", "pdf"] = Query("none")


class PlanOut(BaseModel):
    """Complete plan information for report responses.
    
    Attributes:
        plan_id (int): Unique plan identifier.
        plan_name (str): Name of the plan.
        validity (Optional[int]): Validity period in days.
        most_popular (bool): Whether this is a popular/featured plan.
        plan_type (str): Type (prepaid/postpaid).
        group_id (Optional[int]): ID of plan group category.
        group_name (Optional[str]): Name of plan group.
        description (Optional[dict]): Description of the plan.
        criteria (Optional[dict]): Eligibility criteria.
        created_at (Optional[datetime]): When plan was created.
        created_by (Optional[int]): User ID who created the plan.
        price (int): Plan price.
        status (str): Status (active/inactive).
    """
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


@dataclass
class ReferralReportFilter:
    reward_ids: Optional[List[int]] = Query(None, description="Filter by reward IDs")
    referrer_ids: Optional[List[int]] = Query(None, description="Filter by referrer IDs")
    referred_ids: Optional[List[int]] = Query(None, description="Filter by referred user IDs")
    referrer_phones: Optional[List[str]] = Query(None, description="Filter by referrer phone numbers")
    referred_phones: Optional[List[str]] = Query(None, description="Filter by referred phone numbers")
    statuses: Optional[List[Literal["pending", "earned"]]] = Query(None, description="Filter by reward status")

    min_amount: Optional[float] = Query(None, ge=0, description="Minimum reward amount")
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum reward amount")
    created_from: Optional[datetime] = Query(None, description="Created after this datetime")
    created_to: Optional[datetime] = Query(None, description="Created before this datetime")
    claimed_from: Optional[datetime] = Query(None, description="Claimed after this datetime")
    claimed_to: Optional[datetime] = Query(None, description="Claimed before this datetime")

    order_by: Literal["reward_id", "reward_amount", "status", "created_at", "claimed_at", "referrer_name", "referred_name"] = Query("created_at")
    order_dir: Literal["asc", "desc"] = Query("desc")
    limit: int = Query(0, ge=0, description="0 means no pagination")
    offset: int = Query(0, ge=0, description="0 means no pagination")
    export_type: Literal["none", "csv", "excel", "pdf"] = Query("none")


class ReferralOut(BaseModel):
    """Referral reward information for report responses.
    
    Attributes:
        reward_id (int): Unique reward identifier.
        referrer_id (int): ID of the user who made the referral.
        referred_id (int): ID of the user who was referred.
        reward_amount (Decimal): Monetary reward amount.
        status (str): Status (pending/earned).
        created_at (datetime): When reward was created.
        claimed_at (Optional[datetime]): When reward was claimed/earned.
        referrer_name (Optional[str]): Denormalized referrer user name.
        referrer_phone (Optional[str]): Denormalized referrer phone number.
        referred_name (Optional[str]): Denormalized referred user name.
        referred_phone (Optional[str]): Denormalized referred user phone number.
    """
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


@dataclass
class RolePermissionReportFilter:
    role_permission_ids: Optional[List[int]] = Query(None, description="Filter by role-permission IDs")
    role_ids: Optional[List[int]] = Query(None, description="Filter by role IDs")
    permission_ids: Optional[List[int]] = Query(None, description="Filter by permission IDs")
    role_names: Optional[List[str]] = Query(None, description="Filter by role names")
    resources: Optional[List[str]] = Query(None, description="Filter by resource names")
    read: Optional[bool] = Query(None, description="Filter by read access")
    write: Optional[bool] = Query(None, description="Filter by write access")
    edit: Optional[bool] = Query(None, description="Filter by edit access")
    delete: Optional[bool] = Query(None, description="Filter by delete access")

    order_by: Literal["id", "role_id", "permission_id", "role_name", "resource", "read", "write", "edit", "delete"] = Query("role_id")
    order_dir: Literal["asc", "desc"] = Query("asc")
    limit: int = Query(0, ge=0, description="0 means no pagination")
    offset: int = Query(0, ge=0, description="0 means no pagination")
    export_type: Literal["none", "csv", "excel", "pdf"] = Query("none")


class RolePermissionOut(BaseModel):
    """Role-permission association with denormalized permission details for report responses.
    
    Attributes:
        id (int): Unique role-permission association ID.
        role_id (int): ID of the role.
        permission_id (int): ID of the permission.
        role_name (Optional[str]): Denormalized role name.
        resource (Optional[str]): Denormalized resource name that permission applies to.
        read (bool): Whether read access is granted.
        write (bool): Whether write access is granted.
        edit (bool): Whether edit access is granted.
        delete (bool): Whether delete access is granted.
    """
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


@dataclass
class SessionsReportFilter:
    session_ids: Optional[List[UUID]] = Query(None, description="Filter by session UUIDs")
    user_ids: Optional[List[int]] = Query(None, description="Filter by user IDs")
    is_active: Optional[bool] = Query(None, description="Filter by session activity state")

    jtis: Optional[List[UUID]] = Query(None, description="Filter by JWT IDs (JTI)")
    refresh_tokens_contains: Optional[str] = Query(None, description="Filter refresh tokens containing substring")

    refresh_expires_from: Optional[datetime] = Query(None, description="Refresh token expires after this datetime")
    refresh_expires_to: Optional[datetime] = Query(None, description="Refresh token expires before this datetime")
    login_time_from: Optional[datetime] = Query(None, description="Login time after this datetime")
    login_time_to: Optional[datetime] = Query(None, description="Login time before this datetime")
    last_active_from: Optional[datetime] = Query(None, description="Last active after this datetime")
    last_active_to: Optional[datetime] = Query(None, description="Last active before this datetime")
    revoked_from: Optional[datetime] = Query(None, description="Revoked after this datetime")
    revoked_to: Optional[datetime] = Query(None, description="Revoked before this datetime")

    order_by: Literal["session_id", "user_id", "refresh_token_expires_at", "login_time", "last_active", "is_active", "revoked_at"] = Query("last_active")
    order_dir: Literal["asc", "desc"] = Query("desc")
    limit: int = Query(0, ge=0, description="0 means no pagination")
    offset: int = Query(0, ge=0, description="0 means no pagination")
    export_type: Literal["none", "csv", "excel", "pdf"] = Query("none")


class SessionOut(BaseModel):
    """User session information for report responses.
    
    Attributes:
        session_id (str): Unique session identifier.
        user_id (Optional[int]): ID of the user who owns this session.
        refresh_token (str): Refresh token for session renewal.
        jti (str): JWT Token ID (unique token identifier).
        refresh_token_expires_at (Optional[datetime]): When refresh token expires.
        login_time (Optional[datetime]): When user logged in.
        last_active (Optional[datetime]): Last activity timestamp.
        is_active (bool): Whether session is currently active.
        revoked_at (Optional[datetime]): When session was revoked.
    """
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


@dataclass
class TransactionsReportFilter:
    txn_ids: Optional[List[int]] = Query(None, description="Filter by transaction IDs")
    user_ids: Optional[List[int]] = Query(None, description="Filter by user IDs")
    categories: Optional[List[Literal["wallet", "service"]]] = Query(None, description="Filter by transaction category")
    txn_types: Optional[List[Literal["credit", "debit"]]] = Query(None, description="Filter by transaction type")
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum transaction amount")
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum transaction amount")
    service_types: Optional[List[Literal["prepaid", "postpaid"]]] = Query(None, description="Filter by service type")
    plan_ids: Optional[List[int]] = Query(None, description="Filter by plan IDs")
    offer_ids: Optional[List[int]] = Query(None, description="Filter by offer IDs")
    from_phone_numbers: Optional[List[str]] = Query(None, description="Filter by sender phone numbers")
    to_phone_numbers: Optional[List[str]] = Query(None, description="Filter by receiver phone numbers")
    sources: Optional[List[Literal["recharge", "wallet_topup", "refund", "referral_reward", "autopay"]]] = Query(None, description="Filter by transaction source")
    statuses: Optional[List[Literal["success", "failed", "pending"]]] = Query(None, description="Filter by transaction status")
    payment_methods: Optional[List[Literal["UPI", "Card", "NetBanking", "Wallet"]]] = Query(None, description="Filter by payment method")
    payment_transaction_id_contains: Optional[str] = Query(None, description="Search substring in payment transaction ID")
    created_from: Optional[datetime] = Query(None, description="Created after this datetime")
    created_to: Optional[datetime] = Query(None, description="Created before this datetime")

    order_by: Literal["txn_id", "user_id", "amount", "created_at", "category", "txn_type", "service_type", "source", "status", "payment_method"] = Query("created_at")
    order_dir: Literal["asc", "desc"] = Query("desc")
    limit: int = Query(0, ge=0, description="0 means no pagination")
    offset: int = Query(0, ge=0, description="0 means no pagination")
    export_type: Literal["none", "csv", "excel", "pdf"] = Query("none")


class TransactionOut(BaseModel):
    """Complete transaction record for report responses.
    
    Attributes:
        txn_id (int): Unique transaction identifier.
        user_id (Optional[int]): ID of the user who initiated the transaction.
        category (str): Transaction category (wallet/service/etc).
        txn_type (str): Type of transaction (credit/debit).
        amount (Decimal): Transaction amount.
        service_type (Optional[str]): Service type (prepaid/postpaid).
        plan_id (Optional[int]): ID of plan if plan-related transaction.
        offer_id (Optional[int]): ID of offer if offer-related transaction.
        from_phone_number (Optional[str]): Source phone number.
        to_phone_number (Optional[str]): Destination phone number.
        source (str): Transaction source (recharge/wallet_topup/refund/referral_reward/autopay).
        status (str): Status (success/failed/pending).
        payment_method (Optional[str]): Payment method used (UPI/Card/NetBanking/Wallet).
        payment_transaction_id (Optional[str]): External payment gateway transaction ID.
        created_at (datetime): When transaction was created.
    """
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


@dataclass
class UsersArchiveFilter:
    user_ids: Optional[List[int]] = Query(None, description="Filter by user IDs")
    name_search: Optional[str] = Query(None, description="Partial case-insensitive name search")
    emails: Optional[List[str]] = Query(None, description="Filter by user emails")
    phone_numbers: Optional[List[str]] = Query(None, description="Filter by phone numbers")

    user_types: Optional[List[Literal["prepaid", "postpaid"]]] = Query(None, description="Filter by user type")
    statuses: Optional[List[Literal["active", "blocked"]]] = Query(None, description="Filter by user status")

    min_wallet: Optional[float] = Query(None, ge=0, description="Minimum wallet balance")
    max_wallet: Optional[float] = Query(None, ge=0, description="Maximum wallet balance")

    created_from: Optional[datetime] = Query(None, description="Filter users created after this datetime")
    created_to: Optional[datetime] = Query(None, description="Filter users created before this datetime")
    deleted_from: Optional[datetime] = Query(None, description="Filter users deleted after this datetime")
    deleted_to: Optional[datetime] = Query(None, description="Filter users deleted before this datetime")

    order_by: Literal[
        "user_id", "name", "email", "phone_number", "user_type", "status",
        "wallet_balance", "created_at", "deleted_at"
    ] = Query("deleted_at", description="Field to order by")
    order_dir: Literal["asc", "desc"] = Query("desc", description="Sort order (asc/desc)")

    limit: int = Query(0, ge=0, description="0 means no pagination")
    offset: int = Query(0, ge=0, description="0 means no pagination")

    export_type: Literal["none", "csv", "excel", "pdf"] = Query("none", description="Export format")


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


@dataclass
class UsersReportFilter:
    user_ids: Optional[List[int]] = Query(None, description="Filter by user IDs")
    name_search: Optional[str] = Query(None, description="Case-insensitive partial match on name")
    emails: Optional[List[str]] = Query(None, description="Filter by user emails")
    phone_numbers: Optional[List[str]] = Query(None, description="Filter by phone numbers")

    user_types: Optional[List[Literal["prepaid", "postpaid"]]] = Query(None, description="Filter by user type")
    statuses: Optional[List[Literal["active", "blocked", "deactive"]]] = Query(None, description="Filter by status")

    min_wallet: Optional[float] = Query(None, ge=0, description="Minimum wallet balance")
    max_wallet: Optional[float] = Query(None, ge=0, description="Maximum wallet balance")

    created_from: Optional[datetime] = Query(None, description="Filter users created after this datetime")
    created_to: Optional[datetime] = Query(None, description="Filter users created before this datetime")
    updated_from: Optional[datetime] = Query(None, description="Filter users updated after this datetime")
    updated_to: Optional[datetime] = Query(None, description="Filter users updated before this datetime")

    order_by: Literal[
        "user_id", "name", "email", "phone_number", "user_type", "status",
        "wallet_balance", "created_at", "updated_at"
    ] = Query("created_at", description="Field to order by")
    order_dir: Literal["asc", "desc"] = Query("desc", description="Sort direction")

    limit: int = Query(0, ge=0, description="0 means no pagination")
    offset: int = Query(0, ge=0, description="0 means no pagination")

    export_type: Literal["none", "csv", "excel", "pdf"] = Query("none", description="Export format")


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


@dataclass
class UserTransactionsReportFilter:
    txn_ids: Optional[List[int]] = Query(None, description="Filter by transaction IDs")

    categories: Optional[List[Literal["wallet", "service"]]] = Query(None, description="Filter by category (wallet/service)")
    txn_types: Optional[List[Literal["credit", "debit"]]] = Query(None, description="Filter by transaction type")

    min_amount: Optional[float] = Query(None, ge=0, description="Minimum transaction amount")
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum transaction amount")

    service_types: Optional[List[Literal["prepaid", "postpaid"]]] = Query(None, description="Filter by service type")
    plan_ids: Optional[List[int]] = Query(None, description="Filter by plan IDs")
    offer_ids: Optional[List[int]] = Query(None, description="Filter by offer IDs")

    to_phone_numbers: Optional[List[str]] = Query(None, description="Filter by recipient phone numbers")

    sources: Optional[List[Literal["recharge", "wallet_topup", "refund", "referral_reward", "autopay"]]] = Query(None, description="Filter by transaction source")
    statuses: Optional[List[Literal["success", "failed", "pending"]]] = Query(None, description="Filter by status")
    payment_methods: Optional[List[Literal["UPI", "Card", "NetBanking", "Wallet"]]] = Query(None, description="Filter by payment method")
    payment_transaction_id_contains: Optional[str] = Query(None, description="Search substring in payment transaction ID")

    created_from: Optional[datetime] = Query(None, description="Filter transactions created after this datetime")
    created_to: Optional[datetime] = Query(None, description="Filter transactions created before this datetime")

    order_by: Literal[
        "txn_id", "user_id", "amount", "created_at", "category",
        "txn_type", "service_type", "source", "status", "payment_method"
    ] = Query("created_at", description="Field to order results by")
    order_dir: Literal["asc", "desc"] = Query("desc", description="Sort direction")

    limit: int = Query(0, ge=0, description="0 means no pagination")
    offset: int = Query(0, ge=0, description="0 means no pagination")

    export_type: Literal["none", "csv", "excel", "pdf"] = Query("none", description="Export format for report")


class UserTransactionOut(BaseModel):
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