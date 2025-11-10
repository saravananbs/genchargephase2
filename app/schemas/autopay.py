# app/schemas/autopay.py
from datetime import datetime
from typing import Literal, Optional
from enum import Enum
from pydantic import BaseModel, Field, conint, constr


class AutoPayStatus(str, Enum):
    """
    Enumeration of autopay status values.

    Values:
        enabled: Autopay is active and processing.
        disabled: Autopay is disabled.
    """
    enabled = "enabled"
    disabled = "disabled"


class AutoPayTag(str, Enum):
    """
    Enumeration of autopay tag/frequency values.

    Values:
        onetime: One-time autopay transaction.
        regular: Recurring regular autopay.
    """
    onetime = "onetime"
    regular = "regular"


# ---------- Request Schemas ----------
class AutoPayCreate(BaseModel):
    """
    Schema for creating a new autopay configuration.

    Attributes:
        plan_id (int): ID of the plan for autopay.
        phone_number (str): 10-digit mobile number for transactions.
        tag (AutoPayTag): Autopay type (onetime/regular).
        next_due_date (datetime): Next scheduled date for autopay.
        status (AutoPayStatus): Initial status (default: enabled).
    """
    plan_id: int = Field(..., description="ID of the plan")
    phone_number: str = Field(..., description="10-digit mobile number")
    tag: AutoPayTag = Field(..., description="Type of autopay")
    next_due_date: datetime = Field(..., description="When the next recharge should happen")
    status: AutoPayStatus = Field(AutoPayStatus.enabled, description="Initial status")


class AutoPayUpdate(BaseModel):
    """
    Schema for updating existing autopay configuration.

    Attributes:
        plan_id (Optional[int]): Updated plan ID.
        phone_number (Optional[str]): Updated phone number.
        tag (Optional[AutoPayTag]): Updated autopay type.
        next_due_date (Optional[datetime]): Updated next due date.
        status (Optional[AutoPayStatus]): Updated status.
    """
    plan_id: Optional[int] = None
    phone_number: Optional[str] = None
    tag: Optional[AutoPayTag] = None
    next_due_date: Optional[datetime] = None
    status: Optional[AutoPayStatus] = None


# ---------- Response Schemas ----------
class AutoPayOut(BaseModel):
    """
    Schema for returning autopay information in API responses.

    Attributes:
        autopay_id (int): Unique identifier for the autopay.
        user_id (int): User ID associated with autopay.
        plan_id (int): Plan ID for this autopay.
        status (AutoPayStatus): Current status.
        phone_number (str): Phone number for transactions.
        tag (AutoPayTag): Autopay type.
        next_due_date (datetime): Next scheduled date.
        created_at (datetime): Timestamp of creation.
    """
    autopay_id: int
    user_id: int
    plan_id: int
    status: AutoPayStatus
    phone_number: str
    tag: AutoPayTag
    next_due_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedAutoPay(BaseModel):
    """
    Schema for paginated autopay list responses.

    Attributes:
        items (list[AutoPayOut]): List of autopay records.
        total (int): Total number of autopay records.
        page (int): Current page number.
        size (int): Records per page.
        pages (int): Total number of pages.
    """
    items: list[AutoPayOut]
    total: int
    page: int
    size: int
    pages: int