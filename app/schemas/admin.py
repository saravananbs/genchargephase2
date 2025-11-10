from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal


class AdminCreate(BaseModel):
    """
    Schema for creating a new admin user.

    Attributes:
        name (str): Full name of the admin.
        email (EmailStr): Valid email address (must be unique).
        phone_number (str): Phone number of the admin.
        role_name (str): Name of the role to assign to this admin.
    """
    name: str
    email: EmailStr
    phone_number: str
    role_name: str = Field(..., description="Name of the role to assign")
    
    class Config:
        extra = "forbid"


class AdminUpdate(BaseModel):
    """
    Schema for updating existing admin user information.

    Attributes:
        name (Optional[str]): Updated full name.
        phone_number (Optional[str]): Updated phone number.
        email (Optional[EmailStr]): Updated email address.
        role_name (Optional[str]): Updated role assignment.
    """
    name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    role_name: Optional[str] = None  


class AdminSelfUpdate(BaseModel):
    """
    Schema for admins to update their own profile (limited fields).

    Attributes:
        email (Optional[EmailStr]): Updated email address.
    """
    email: Optional[EmailStr] = None

class AdminListFilters(BaseModel):
    """
    Schema for filtering and paginating admin list queries.

    Attributes:
        name (Optional[str]): Filter by admin name (partial match).
        email (Optional[str]): Filter by email address.
        phone_number (Optional[str]): Filter by phone number.
        role_name (Optional[str]): Filter by assigned role.
        skip (int): Number of records to skip (default: 0).
        limit (int): Maximum records to return (default: 10).
        sort_by (Optional[str]): Field to sort by (name/email/created_at/updated_at).
        sort_order (Optional[str]): Sort direction (asc/desc, default: asc).
    """
    name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    role_name: Optional[str] = None
    skip: int = 0
    limit: int = 10
    sort_by: Optional[Literal["name", "email", "created_at", "updated_at"]] = None
    sort_order: Optional[Literal["asc", "desc"]] = "asc"

class AdminOut(BaseModel):
    """
    Schema for returning admin user information in responses.

    Attributes:
        admin_id (int): Unique identifier for the admin.
        name (str): Full name of the admin.
        email (EmailStr): Email address of the admin.
        phone_number (str): Phone number of the admin.
        role_id (Optional[int]): ID of the assigned role.
        created_at (Optional[datetime]): Timestamp of admin creation.
        updated_at (Optional[datetime]): Timestamp of last update.
    """
    admin_id: int
    name: str
    email: EmailStr
    phone_number: str
    role_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
