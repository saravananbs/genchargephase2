from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum
from datetime import datetime


class PlanType(str, Enum):
    prepaid = "prepaid"
    postpaid = "postpaid"


class PlanStatus(str, Enum):
    active = "active"
    inactive = "inactive"


class PlanBase(BaseModel):
    plan_name: str
    validity: Optional[int] = None
    most_popular: bool = False
    plan_type: PlanType
    group_id: Optional[int] = None
    description: Optional[str] = None
    criteria: Optional[Any] = None
    price: int


class PlanCreate(PlanBase):
    pass

class PlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    validity: Optional[int] = None
    most_popular: Optional[bool] = None
    plan_type: Optional[PlanType] = None
    group_id: Optional[int] = None
    description: Optional[str] = None
    criteria: Optional[Any] = None
    status: Optional[PlanStatus] = None


class PlanResponse(PlanBase):
    plan_id: int
    status: PlanStatus
    created_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class UserPlanResponse(PlanBase):
    plan_id: int

    class Config:
        from_attributes = True


class PlanFilter(BaseModel):
    search: Optional[str] = Field(None, description="Search in plan name or description")
    type: Optional[PlanType] = Field(None, description="Filter by plan type")
    status: Optional[PlanStatus] = Field(None, description="Filter by status")
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    order_by: str = Field("plan_id", description="Order field (plan_id, plan_name, validity, created_at)")
    order_dir: str = Field("asc", pattern="^(asc|desc)$")
