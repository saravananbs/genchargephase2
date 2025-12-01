from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum
from datetime import datetime


class PlanType(str, Enum):
    """
    Enumeration of plan service types.

    Values:
        prepaid: Prepaid plan type.
        postpaid: Postpaid plan type.
    """
    prepaid = "prepaid"
    postpaid = "postpaid"


class PlanStatus(str, Enum):
    """
    Enumeration of plan availability status.

    Values:
        active: Plan is currently active.
        inactive: Plan is inactive.
    """
    active = "active"
    inactive = "inactive"


class PlanBase(BaseModel):
    """
    Base schema for plan data shared across plan endpoints.

    Attributes:
        plan_name (str): Name of the plan.
        validity (Optional[int]): Validity duration in days.
        most_popular (bool): Flag for popular/featured plans (default: False).
        plan_type (PlanType): Service type (prepaid/postpaid).
        group_id (Optional[int]): Group ID for plan categorization.
        description (Optional[str]): Detailed plan description.
        criteria (Optional[Any]): Eligibility criteria as JSON.
        price (int): Plan price in minor currency units.
    """
    plan_name: str
    validity: Optional[int] = None
    most_popular: bool = False
    plan_type: PlanType
    group_id: Optional[int] = None
    description: Optional[str] = None
    criteria: Optional[Any] = None
    price: int


class PlanCreate(PlanBase):
    """
    Schema for creating a new plan (inherits all fields from PlanBase).
    """
    pass

class PlanUpdate(BaseModel):
    """
    Schema for updating plan information.

    All fields optional to allow partial updates.

    Attributes:
        plan_name (Optional[str]): Updated plan name.
        validity (Optional[int]): Updated validity in days.
        most_popular (Optional[bool]): Updated popular flag.
        plan_type (Optional[PlanType]): Updated service type.
        group_id (Optional[int]): Updated group ID.
        description (Optional[str]): Updated description.
        criteria (Optional[Any]): Updated eligibility criteria.
        status (Optional[PlanStatus]): Updated plan status.
    """
    plan_name: Optional[str] = None
    validity: Optional[int] = None
    most_popular: Optional[bool] = None
    plan_type: Optional[PlanType] = None
    group_id: Optional[int] = None
    description: Optional[str] = None
    criteria: Optional[Any] = None
    status: Optional[PlanStatus] = None


class PlanResponse(PlanBase):
    """
    Schema for returning plan information in responses.

    Inherits from PlanBase. Attributes:
        plan_id (int): Unique plan identifier.
        status (PlanStatus): Current plan status.
        created_by (Optional[int]): Admin ID who created plan.
        created_at (datetime): Timestamp of plan creation.
    """
    plan_id: int
    status: PlanStatus
    created_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class UserPlanResponse(PlanBase):
    """
    Schema for returning plan information to end users.

    Inherits from PlanBase. Attributes:
        plan_id (int): Unique plan identifier.
    """
    plan_id: int

    class Config:
        from_attributes = True


class PlanFilter(BaseModel):
    """
    Schema for filtering plan list queries.

    Attributes:
        search (Optional[str]): Search text in plan name or description.
        type (Optional[PlanType]): Filter by plan service type.
    """
    search: Optional[str] = Field(None, description="Search in plan name or description")
    type: Optional[PlanType] = Field(None, description="Filter by plan type")
    status: Optional[PlanStatus] = Field(None, description="Filter by status")
    page: int = Field(0, ge=0)
    limit: int = Field(0, ge=0, le=100)
    order_by: str = Field("plan_id", description="Order field (plan_id, plan_name, validity, created_at)")
    order_dir: str = Field("asc", pattern="^(asc|desc)$")
