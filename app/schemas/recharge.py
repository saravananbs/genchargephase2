from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field, field_validator
from ..models.plans import PlanType, PlanStatus
from ..models.offers import OfferStatus
from ..models.transactions import (
    TransactionCategory, TransactionType, TransactionSource,
    TransactionStatus, PaymentMethod, ServiceType,
)
from ..models.current_active_plans import CurrentPlanStatus
from ..schemas.users import UserResponse
from enum import Enum


# ------------------- Plan -------------------
class PlanOut(BaseModel):
    """Complete plan information for recharge/subscription responses.
    
    Attributes:
        plan_id (int): Unique identifier for the plan.
        plan_name (str): Name of the plan.
        validity (Optional[int]): Validity period in days.
        most_popular (bool): Whether this is a popular/featured plan. Defaults to False.
        plan_type (PlanType): Type of plan (prepaid/postpaid).
        group_id (Optional[int]): ID of the plan group category.
        description (Optional[str]): Description of the plan.
        criteria (Optional[dict]): JSON criteria for plan eligibility.
        status (PlanStatus): Current status (active/inactive).
        created_at (datetime): Timestamp when plan was created.
    """
    plan_id: int
    plan_name: str
    validity: Optional[int] = None
    most_popular: bool = False
    plan_type: PlanType
    group_id: Optional[int] = None
    description: Optional[str] = None
    criteria: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PlanListResponse(BaseModel):
    """Paginated response for plan list queries.
    
    Attributes:
        plans (List[PlanOut]): List of plan objects.
        total (int): Total number of plans matching query.
        page (int): Current page number.
        size (int): Items per page.
        pages (int): Total number of pages.
    """
    plans: List[PlanOut]
    total: int
    page: int
    size: int
    pages: int


# ------------------- Offer -------------------
class OfferOut(BaseModel):
    """Complete offer information for recharge/subscription responses.
    
    Attributes:
        offer_id (int): Unique identifier for the offer.
        offer_name (str): Name of the offer.
        offer_validity (Optional[int]): Validity period in days.
        offer_type_id (Optional[int]): ID of the offer type category.
        is_special (bool): Whether this is a special/featured offer. Defaults to False.
        criteria (Optional[dict]): JSON criteria for offer eligibility.
        description (Optional[str]): Description of the offer.
        status (OfferStatus): Current status (active/inactive).
        created_at (datetime): Timestamp when offer was created.
    """
    offer_id: int
    offer_name: str
    offer_validity: Optional[int] = None
    offer_type_id: Optional[int] = None
    is_special: bool = False
    criteria: Optional[dict] = None
    description: Optional[str] = None
    status: OfferStatus
    created_at: datetime

    class Config:
        from_attributes = True


# ------------------- CurrentActivePlan -------------------
class CurrentActivePlanOut(BaseModel):
    """Information about user's current active plan subscription.
    
    Attributes:
        id (int): Unique subscription record ID.
        user_id (int): ID of the user who owns this plan.
        plan_id (int): ID of the subscribed plan.
        phone_number (str): Associated phone number for the plan.
        valid_from (datetime): When the plan becomes active.
        valid_to (datetime): When the plan expires.
        status (CurrentPlanStatus): Current subscription status.
        plan (PlanOut): Nested plan details.
    """
    id: int
    user_id: int
    plan_id: int
    phone_number: str
    valid_from: datetime
    valid_to: datetime
    status: CurrentPlanStatus
    plan: PlanOut

    class Config:
        from_attributes = True


class CurrentPlanListResponse(BaseModel):
    """Paginated response for current active plans list queries.
    
    Attributes:
        plans (List[CurrentActivePlanOut]): List of active plan objects.
        total (int): Total number of plans matching query.
        page (int): Current page number.
        size (int): Items per page.
        pages (int): Total number of pages.
    """
    plans: List[CurrentActivePlanOut]
    total: int
    page: int
    size: int
    pages: int


# ------------------- Transaction -------------------
class TransactionOut(BaseModel):
    """Complete transaction record information for transaction list responses.
    
    Attributes:
        txn_id (int): Unique transaction identifier.
        user_id (Optional[int]): ID of the user who initiated the transaction.
        category (TransactionCategory): Transaction category (recharge/offer/wallet/etc).
        txn_type (TransactionType): Type of transaction (credit/debit/refund).
        amount (Decimal): Transaction amount.
        service_type (Optional[ServiceType]): Service type associated with transaction.
        plan_id (Optional[int]): ID of plan if transaction is plan-related.
        offer_id (Optional[int]): ID of offer if transaction is offer-related.
        from_phone_number (Optional[str]): Source phone number.
        to_phone_number (Optional[str]): Destination phone number.
        source (TransactionSource): Source of transaction (recharge/autopay/referral/etc).
        status (TransactionStatus): Current status (pending/completed/failed).
        payment_method (Optional[PaymentMethod]): Payment method used.
        payment_transaction_id (Optional[str]): External payment gateway transaction ID.
        created_at (datetime): Timestamp when transaction was created.
        user (Optional[UserResponse]): Nested user details.
    """
    txn_id: int
    user_id: Optional[int] = None
    category: TransactionCategory
    txn_type: TransactionType
    amount: Decimal
    service_type: Optional[ServiceType] = None
    plan_id: Optional[int] = None
    offer_id: Optional[int] = None
    from_phone_number: Optional[str] = None
    to_phone_number: Optional[str] = None
    source: TransactionSource
    status: TransactionStatus
    payment_method: Optional[PaymentMethod] = None
    payment_transaction_id: Optional[str] = None
    created_at: datetime
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Paginated response for transaction list queries.
    
    Attributes:
        transactions (List[TransactionOut]): List of transaction objects.
        total (int): Total number of transactions matching query.
        page (int): Current page number.
        size (int): Items per page.
        pages (int): Total number of pages.
    """
    transactions: List[TransactionOut]
    total: int
    page: int
    size: int
    pages: int


# ------------------- Request models -------------------
class RechargeRequest(BaseModel):
    """Request payload for initiating a plan recharge.
    
    Attributes:
        phone_number (str): Target mobile number for recharge.
        plan_id (int): ID of the plan to subscribe.
        offer_id (Optional[int]): Optional offer ID to apply to this recharge.
        payment_method (PaymentMethod): Payment method used for the transaction.
        source (TransactionSource): Source of transaction (recharge/autopay/referral/etc).
        activation_mode (Literal['activate', 'queue']): When to activate the plan. 'activate' for immediate, 'queue' for scheduled. Defaults to 'activate'.
    """
    phone_number: str = Field(..., description="Target mobile number for recharge")
    plan_id: int = Field(..., description="ID of the plan to subscribe")
    offer_id: Optional[int] = Field(None, description="Optional offer to apply")
    payment_method: PaymentMethod = Field(..., description="Payment method used")
    source: TransactionSource = Field(
        ..., description="Source of the transaction (recharge, autopay, etc.)"
    )
    activation_mode: Literal["activate", "queue"] = "activate"


class WalletTopupRequest(BaseModel):
    """Request payload for wallet top-up transaction.
    
    Attributes:
        amount (Decimal): Amount to top-up (must be > 0).
        phone_number (Optional[str]): Phone number to top-up. If omitted, uses authenticated user's wallet.
        payment_method (PaymentMethod): Payment method used for the transaction.
    """
    amount: Decimal = Field(..., gt=0, description="Amount to top-up")
    phone_number: Optional[str] = Field(
        None, description="If omitted, top-up the authenticated user's wallet"
    )
    payment_method: PaymentMethod = Field(..., description="Payment method used")

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v


class ApplyOfferRequest(BaseModel):
    """Request payload for applying an offer to a plan.
    
    Attributes:
        offer_id (int): ID of the offer to apply.
        plan_id (int): ID of the plan.
        phone_number (str): Target mobile number (must be exactly 10 digits).
    """
    offer_id: int = Field(..., description="ID of the offer")
    plan_id: int = Field(..., description="ID of the plan")
    phone_number: str = Field(..., description="Target mobile number")

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 10:
            raise ValueError("Phone number must be exactly 10 digits")
        return v
    
class SortOrder(str, Enum):
    """Enumeration for sorting order in queries.
    
    Attributes:
        asc (str): Ascending order.
        desc (str): Descending order.
    """
    asc = "asc"
    desc = "desc"

class UserCurrentPlanFilterParams(BaseModel):
    """Filter parameters for user's current active plans query.
    
    Attributes:
        page (int): Page number for pagination (1-indexed). Minimum 1.
        size (int): Items per page. Between 1-500. Defaults to 10.
        plan_id (Optional[int]): Exact plan ID to filter by.
        status (Optional[CurrentPlanStatus]): Plan status filter.
        valid_from_start (Optional[date]): Inclusive start date for plan validity start.
        valid_from_end (Optional[date]): Inclusive end date for plan validity start.
        valid_to_start (Optional[date]): Inclusive start date for plan expiry.
        valid_to_end (Optional[date]): Inclusive end date for plan expiry.
        validity_days_min (Optional[int]): Minimum plan validity in days.
        validity_days_max (Optional[int]): Maximum plan validity in days.
        sort_by (Optional[str]): Column to sort by (valid_from or valid_to).
        sort_order (Optional[SortOrder]): Sort direction (asc/desc). Defaults to desc.
    """
    # pagination
    page: int = Field(0, ge=0, description="Page number (1-based)")
    size: int = Field(0, ge=0, le=500, description="Items per page")

    # existing filters
    plan_id: Optional[int] = Field(None, description="Exact plan_id")
    status: Optional[CurrentPlanStatus] = Field(None, description="Plan status")

    # date ranges
    valid_from_start: Optional[date] = Field(
        None, description="Inclusive start of `valid_from`"
    )
    valid_from_end: Optional[date] = Field(
        None, description="Inclusive end of `valid_from`"
    )
    valid_to_start: Optional[date] = Field(
        None, description="Inclusive start of `valid_to`"
    )
    valid_to_end: Optional[date] = Field(
        None, description="Inclusive end of `valid_to`"
    )

    # validity length (in days)
    validity_days_min: Optional[int] = Field(
        None, ge=0, description="Minimum validity length in days"
    )
    validity_days_max: Optional[int] = Field(
        None, ge=0, description="Maximum validity length in days"
    )

    # sorting
    sort_by: Optional[str] = Field(
        None,
        description="Column to sort by",
        pattern="^(valid_from|valid_to)$"
    )
    sort_order: Optional[SortOrder] = Field(
        SortOrder.desc,
        description="Sort direction"
    )

class CurrentPlanFilterParams(BaseModel):
    """Advanced filter and pagination parameters for current active plans queries.
    
    Supports phone number search, plan filtering, date ranges, and validity length filtering.
    
    Attributes:
        page (int): Page number for pagination (1-indexed). Minimum 1.
        size (int): Items per page. Between 1-500. Defaults to 10.
        phone_number (Optional[str]): Exact phone number match.
        phone_number_like (Optional[str]): Partial phone number search using SQL LIKE pattern.
        plan_id (Optional[int]): Exact plan ID to filter by.
        status (Optional[CurrentPlanStatus]): Plan status filter.
        valid_from_start (Optional[date]): Inclusive start date for plan validity start.
        valid_from_end (Optional[date]): Inclusive end date for plan validity start.
        valid_to_start (Optional[date]): Inclusive start date for plan expiry.
        valid_to_end (Optional[date]): Inclusive end date for plan expiry.
        validity_days_min (Optional[int]): Minimum plan validity in days.
        validity_days_max (Optional[int]): Maximum plan validity in days.
        sort_by (Optional[str]): Column to sort by (valid_from or valid_to).
        sort_order (Optional[SortOrder]): Sort direction (asc/desc). Defaults to desc.
    """
    # pagination
    page: int = Field(0, ge=0, description="Page number (1-based)")
    size: int = Field(0, ge=0, le=500, description="Items per page")

    # existing filters
    phone_number: Optional[str] = Field(None, description="Exact phone number")
    phone_number_like: Optional[str] = Field(
        None,
        description="LIKE search on phone_number (SQL `%value%`)",
        example="12345"
    )
    plan_id: Optional[int] = Field(None, description="Exact plan_id")
    status: Optional[CurrentPlanStatus] = Field(None, description="Plan status")

    # date ranges
    valid_from_start: Optional[date] = Field(
        None, description="Inclusive start of `valid_from`"
    )
    valid_from_end: Optional[date] = Field(
        None, description="Inclusive end of `valid_from`"
    )
    valid_to_start: Optional[date] = Field(
        None, description="Inclusive start of `valid_to`"
    )
    valid_to_end: Optional[date] = Field(
        None, description="Inclusive end of `valid_to`"
    )

    # validity length (in days)
    validity_days_min: Optional[int] = Field(
        None, ge=0, description="Minimum validity length in days"
    )
    validity_days_max: Optional[int] = Field(
        None, ge=0, description="Maximum validity length in days"
    )

    # sorting
    sort_by: Optional[str] = Field(
        None,
        description="Column to sort by",
        pattern="^(valid_from|valid_to)$"
    )
    sort_order: Optional[SortOrder] = Field(
        SortOrder.desc,
        description="Sort direction"
    )


class SortBy(str, Enum):
    """Enumeration for transaction sorting fields.
    
    Attributes:
        created_at (str): Sort by transaction creation date.
        amount (str): Sort by transaction amount.
    """
    created_at = "created_at"
    amount = "amount"

class TransactionFilterParams(BaseModel):
    """Advanced filter and pagination parameters for transaction queries.
    
    Supports filtering by category, status, amount ranges, date ranges, and phone numbers.
    
    Attributes:
        page (int): Page number (1-indexed). Minimum 1.
        size (int): Items per page. 0 returns all rows. Maximum 10,000. Defaults to 10.
        user_id (Optional[int]): Exact user ID to filter by.
        category (Optional[TransactionCategory]): Transaction category filter.
        txn_type (Optional[TransactionType]): Transaction type (credit/debit) filter.
        service_type (Optional[ServiceType]): Service type (prepaid/postpaid) filter.
        source (Optional[TransactionSource]): Transaction source filter.
        status (Optional[TransactionStatus]): Transaction status filter.
        payment_method (Optional[PaymentMethod]): Payment method filter.
        from_phone_number (Optional[str]): Exact source phone number.
        from_phone_number_like (Optional[str]): Partial source phone number search.
        to_phone_number (Optional[str]): Exact destination phone number.
        to_phone_number_like (Optional[str]): Partial destination phone number search.
        amount_min (Optional[float]): Minimum transaction amount (inclusive).
        amount_max (Optional[float]): Maximum transaction amount (inclusive).
        created_at_start (Optional[date]): Inclusive start date for created_at.
        created_at_end (Optional[date]): Inclusive end date for created_at.
        sort_by (SortBy): Sort by created_at or amount. Defaults to created_at.
        sort_order (SortOrder): Sort direction (asc/desc). Defaults to desc.
    """
    # ---------- pagination ----------
    page: int = Field(1, ge=1, description="Page number (1-based)")
    size: int = Field(
        10,
        ge=0,
        le=10_000,
        description="Items per page – `0` = return **all** rows",
    )

    # ---------- simple filters ----------
    user_id: Optional[int] = Field(None, description="Exact user_id")
    category: Optional[TransactionCategory] = None
    txn_type: Optional[TransactionType] = None
    service_type: Optional[ServiceType] = None
    source: Optional[TransactionSource] = None
    status: Optional[TransactionStatus] = None
    payment_method: Optional[PaymentMethod] = None

    # ---------- phone numbers ----------
    from_phone_number: Optional[str] = Field(None, description="Exact `from_phone_number`")
    from_phone_number_like: Optional[str] = Field(
        None,
        description="LIKE search on `from_phone_number` (`%value%`)"
    )
    to_phone_number: Optional[str] = Field(None, description="Exact `to_phone_number`")
    to_phone_number_like: Optional[str] = Field(
        None,
        description="LIKE search on `to_phone_number` (`%value%`)"
    )

    # ---------- amount range ----------
    amount_min: Optional[float] = Field(None, ge=0, description="Minimum amount (inclusive)")
    amount_max: Optional[float] = Field(None, ge=0, description="Maximum amount (inclusive)")

    # ---------- created_at range ----------
    created_at_start: Optional[date] = Field(
        None, description="Inclusive start date of `created_at`"
    )
    created_at_end: Optional[date] = Field(
        None, description="Inclusive end date of `created_at`"
    )

    # ---------- sorting ----------
    sort_by: SortBy = SortBy.created_at
    sort_order: SortOrder = SortOrder.desc

class UserTransactionFilterParams(BaseModel):
    """Filter and pagination parameters for user's transaction queries.
    
    Similar to TransactionFilterParams but focused on a single user's transactions.
    Does not include user_id or from_phone_number filtering (those are user-specific).
    
    Attributes:
        page (int): Page number (1-indexed). Minimum 1.
        size (int): Items per page. 0 returns all rows. Maximum 10,000. Defaults to 10.
        category (Optional[TransactionCategory]): Transaction category filter.
        txn_type (Optional[TransactionType]): Transaction type (credit/debit) filter.
        service_type (Optional[ServiceType]): Service type (prepaid/postpaid) filter.
        source (Optional[TransactionSource]): Transaction source filter.
        status (Optional[TransactionStatus]): Transaction status filter.
        payment_method (Optional[PaymentMethod]): Payment method filter.
        to_phone_number (Optional[str]): Exact destination phone number.
        to_phone_number_like (Optional[str]): Partial destination phone number search.
        amount_min (Optional[float]): Minimum transaction amount (inclusive).
        amount_max (Optional[float]): Maximum transaction amount (inclusive).
        created_at_start (Optional[date]): Inclusive start date for created_at.
        created_at_end (Optional[date]): Inclusive end date for created_at.
        sort_by (SortBy): Sort by created_at or amount. Defaults to created_at.
        sort_order (SortOrder): Sort direction (asc/desc). Defaults to desc.
    """
    # ---------- pagination ----------
    page: int = Field(1, ge=1, description="Page number (1-based)")
    size: int = Field(
        10,
        ge=0,
        le=10_000,
        description="Items per page – `0` = return **all** rows",
    )

    # ---------- simple filters ----------
    category: Optional[TransactionCategory] = None
    txn_type: Optional[TransactionType] = None
    service_type: Optional[ServiceType] = None
    source: Optional[TransactionSource] = None
    status: Optional[TransactionStatus] = None
    payment_method: Optional[PaymentMethod] = None

    # ---------- phone numbers ----------
    to_phone_number: Optional[str] = Field(None, description="Exact `to_phone_number`")
    to_phone_number_like: Optional[str] = Field(
        None,
        description="LIKE search on `to_phone_number` (`%value%`)"
    )

    # ---------- amount range ----------
    amount_min: Optional[float] = Field(None, ge=0, description="Minimum amount (inclusive)")
    amount_max: Optional[float] = Field(None, ge=0, description="Maximum amount (inclusive)")

    # ---------- created_at range ----------
    created_at_start: Optional[date] = Field(
        None, description="Inclusive start date of `created_at`"
    )
    created_at_end: Optional[date] = Field(
        None, description="Inclusive end date of `created_at`"
    )

    # ---------- sorting ----------
    sort_by: SortBy = SortBy.created_at
    sort_order: SortOrder = SortOrder.desc