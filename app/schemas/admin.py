from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from ..models.admins import AdminStatus


class AdminCreate(BaseModel):
    name: str
    email: EmailStr
    phone_number: str
    created_at: Optional[datetime] = datetime.now()
    updated_at: Optional[datetime] = datetime.now()
    role_name: str = Field(..., description="Name of the role to assign")


class AdminUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[str] = None
    role_name: Optional[str] = None  


class AdminSelfUpdate(BaseModel):
    email: Optional[EmailStr] = None

class AdminListFilters(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    status: Optional[AdminStatus] = None
    role_name: Optional[str] = None
    skip: int = 0
    limit: int = 10
    sort_by: Optional[Literal["name", "email", "created_at", "updated_at"]] = None
    sort_order: Optional[Literal["asc", "desc"]] = "asc"

class AdminOut(BaseModel):
    admin_id: int
    name: str
    email: EmailStr
    phone_number: str
    status: Optional[str] = None
    role_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
