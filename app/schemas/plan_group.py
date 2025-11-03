from pydantic import BaseModel, Field
from typing import Optional, List

class PlanGroupBase(BaseModel):
    group_name: str

class PlanGroupCreate(PlanGroupBase):
    pass

class PlanGroupUpdate(BaseModel):
    group_name: Optional[str] = None


class PlanGroupFilter(BaseModel):
    search: Optional[str] = Field(None, description="Filter by partial group name")
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(10, ge=1, le=100, description="Items per page")
    order_by: str = Field("group_id", description="Column to order by (group_id or group_name)")
    order_dir: str = Field("asc", pattern="^(asc|desc)$", description="Order direction")

class PlanGroupResponse(BaseModel):
    group_id: int
    group_name: str

    class Config:
        from_attributes = True