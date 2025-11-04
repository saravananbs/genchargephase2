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
    plan_id: int
    plan_name: str
    validity: Optional[int] = None
    most_popular: bool = False
    plan_type: PlanType
    group_id: Optional[int] = None
    description: Optional[str] = None
    criteria: Optional[dict] = None
    status: PlanStatus
    created_at: datetime

    class Config:
        from_attributes = True


class PlanListResponse(BaseModel):
    plans: List[PlanOut]
    total: int
    page: int
    size: int
    pages: int


# ------------------- Offer -------------------
class OfferOut(BaseModel):
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
    plans: List[CurrentActivePlanOut]
    total: int
    page: int
    size: int
    pages: int


# ------------------- Transaction -------------------
class TransactionOut(BaseModel):
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
    transactions: List[TransactionOut]
    total: int
    page: int
    size: int
    pages: int


# ------------------- Request models -------------------
class RechargeRequest(BaseModel):
    phone_number: str = Field(..., description="Target mobile number for recharge")
    plan_id: int = Field(..., description="ID of the plan to subscribe")
    offer_id: Optional[int] = Field(None, description="Optional offer to apply")
    payment_method: PaymentMethod = Field(..., description="Payment method used")
    source: TransactionSource = Field(
        ..., description="Source of the transaction (recharge, autopay, etc.)"
    )
    activation_mode: Literal["activate", "queue"] = "activate"


class WalletTopupRequest(BaseModel):
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
    asc = "asc"
    desc = "desc"

class UserCurrentPlanFilterParams(BaseModel):
    # pagination
    page: int = Field(1, ge=1, description="Page number (1-based)")
    size: int = Field(10, ge=1, le=500, description="Items per page")

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
    # pagination
    page: int = Field(1, ge=1, description="Page number (1-based)")
    size: int = Field(10, ge=1, le=500, description="Items per page")

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
    created_at = "created_at"
    amount = "amount"

class TransactionFilterParams(BaseModel):
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