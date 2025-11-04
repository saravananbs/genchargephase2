# app/schemas/autopay.py
from datetime import datetime
from typing import Literal, Optional
from enum import Enum
from pydantic import BaseModel, Field, conint, constr


class AutoPayStatus(str, Enum):
    enabled = "enabled"
    disabled = "disabled"


class AutoPayTag(str, Enum):
    onetime = "onetime"
    regular = "regular"


# ---------- Request Schemas ----------
class AutoPayCreate(BaseModel):
    plan_id: int = Field(..., description="ID of the plan")
    phone_number: str = Field(..., description="10-digit mobile number")
    tag: AutoPayTag = Field(..., description="Type of autopay")
    next_due_date: datetime = Field(..., description="When the next recharge should happen")
    status: AutoPayStatus = Field(AutoPayStatus.enabled, description="Initial status")


class AutoPayUpdate(BaseModel):
    plan_id: Optional[int] = None
    phone_number: Optional[str] = None
    tag: Optional[AutoPayTag] = None
    next_due_date: Optional[datetime] = None
    status: Optional[AutoPayStatus] = None


# ---------- Response Schemas ----------
class AutoPayOut(BaseModel):
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
    items: list[AutoPayOut]
    total: int
    page: int
    size: int
    pages: int