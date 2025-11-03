# schemas/users.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum

class UserBase(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: str
    referral_code: Optional[str] = None
    user_type: str
    status: str = "active"
    wallet_balance: float = 0.0
    class Config:
        from_attributes = True

class UserCreatenew(UserBase):
    referee_code: Optional[str] = None
    created_at: datetime = datetime.now()


class UserType(str, Enum):
    prepaid = "prepaid"
    postpaid = "postpaid"

class UserStatus(str, Enum):
    active = "active"
    blocked = "blocked"

# ---------- Admin ----------
class UserListFilters(BaseModel):
    name: Optional[str] = None
    status: Optional[UserStatus] = None
    user_type: Optional[UserType] = None
    skip: int = 0
    limit: int = 10
    sort_by: Optional[Literal["name", "created_at", "wallet_balance"]] = None
    sort_order: Optional[Literal["asc", "desc"]] = "asc"


class UserResponse(UserBase):
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ---------- User ----------
class UserEditEmail(BaseModel):
    email: EmailStr


class UserSwitchType(BaseModel):
    user_type: UserType


class UserDeactivate(BaseModel):
    reason: Optional[str] = None


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    referee_code: Optional[str] = None

class UserRegisterResponse(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    phone_number: str
    referral_code: Optional[str]
    referee_code: Optional[str]
    user_type: str
    status: str
    wallet_balance: float

    class Config:
        from_attributes = True

class UserPreferenceBase(BaseModel):
    email_notification: bool = True
    sms_notification: bool = True
    marketing_communication: bool = False
    recharge_remainders: bool = True
    promotional_offers: bool = False
    transactional_alerts: bool = True
    data_analytics: bool = True
    third_party_integrations: bool = False

class UserPreferenceUpdate(UserPreferenceBase):
    pass

class UserPreferenceResponse(UserPreferenceBase):
    user_id: int

    class Config:
        from_attributes = True
