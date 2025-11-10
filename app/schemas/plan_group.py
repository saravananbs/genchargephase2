from pydantic import BaseModel, Field
from typing import Optional, List

class PlanGroupBase(BaseModel):
    """Base schema for plan group data.
    
    Attributes:
        group_name (str): Name of the plan group category.
    """
    group_name: str

class PlanGroupCreate(PlanGroupBase):
    """Schema for creating a new plan group.
    
    Inherits all fields from PlanGroupBase for plan group creation.
    """
    pass

class PlanGroupUpdate(BaseModel):
    """Schema for updating an existing plan group with optional fields.
    
    Attributes:
        group_name (Optional[str]): Updated name of the plan group.
    """
    group_name: Optional[str] = None


class PlanGroupFilter(BaseModel):
    """Filter and pagination parameters for plan group list queries.
    
    Attributes:
        search (Optional[str]): Search text to filter plan groups by partial group name.
        page (int): Page number for pagination (1-indexed). Minimum 1.
        limit (int): Items per page. Between 1 and 100. Defaults to 10.
        order_by (str): Field to order results by. Options: group_id or group_name.
        order_dir (str): Order direction (asc/desc). Defaults to asc.
    """
    search: Optional[str] = Field(None, description="Filter by partial group name")
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(10, ge=1, le=100, description="Items per page")
    order_by: str = Field("group_id", description="Column to order by (group_id or group_name)")
    order_dir: str = Field("asc", pattern="^(asc|desc)$", description="Order direction")

class PlanGroupResponse(BaseModel):
    """Complete plan group response for API endpoints.
    
    Attributes:
        group_id (int): Unique identifier for the plan group.
        group_name (str): Name of the plan group.
    """
    group_id: int
    group_name: str

    class Config:
        from_attributes = True