# schemas/users.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum

class UserBase(BaseModel):
    """
    Base schema for user data shared across multiple user endpoints.

    Attributes:
        name (Optional[str]): Full name of the user.
        email (Optional[EmailStr]): Valid email address.
        phone_number (str): Unique phone number for the user.
        referral_code (Optional[str]): Unique referral code generated for user.
        user_type (str): Service type (prepaid/postpaid).
        status (str): Account status (default: active).
        wallet_balance (float): Current wallet balance (default: 0.0).
        referee_code (Optional[str]): Referral code of referrer.
    """
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: str
    referral_code: Optional[str] = None
    user_type: Optional[str] = None
    status: str = "active"
    wallet_balance: float = 0.0
    referee_code: Optional[str] = None
    class Config:
        from_attributes = True

class UserCreatenew(UserBase):
    """
    Schema for creating a new user account.

    Inherits from UserBase. Attributes:
        referee_code (Optional[str]): Optional referral code of referring user.
        created_at (datetime): Creation timestamp (default: now).
    """
    referee_code: Optional[str] = None
    created_at: datetime = datetime.now()


class UserType(str, Enum):
    """
    Enumeration of user service types.

    Values:
        prepaid: Prepaid service user.
        postpaid: Postpaid service user.
    """
    prepaid = "prepaid"
    postpaid = "postpaid"

class UserStatus(str, Enum):
    """
    Enumeration of user account status values.

    Values:
        active: Account is active.
        blocked: Account has been blocked.
    """
    active = "active"
    blocked = "blocked"

# ---------- Admin ----------
class UserListFilters(BaseModel):
    """
    Schema for filtering and paginating user list queries (admin use).

    Attributes:
        name (Optional[str]): Filter by user name (partial match).
        status (Optional[UserStatus]): Filter by account status.
        user_type (Optional[UserType]): Filter by service type.
        skip (int): Number of records to skip (default: 0).
        limit (int): Maximum records to return (default: 10).
        sort_by (Optional[str]): Field to sort by (name/created_at/wallet_balance).
        sort_order (Optional[str]): Sort direction (asc/desc, default: asc).
    """
    name: Optional[str] = None
    status: Optional[UserStatus] = None
    user_type: Optional[UserType] = None
    skip: int = 0
    limit: int = 0
    sort_by: Optional[Literal["name", "created_at", "wallet_balance"]] = None
    sort_order: Optional[Literal["asc", "desc"]] = "asc"


class UserResponse(UserBase):
    """
    Schema for returning user information in API responses.

    Inherits from UserBase. Attributes:
        user_id (int): Unique user identifier.
        created_at (datetime): Account creation timestamp.
        updated_at (Optional[datetime]): Last account update timestamp.
    """
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ---------- User ----------
class UserEditEmail(BaseModel):
    """
    Schema for user email update request.

    Attributes:
        email (EmailStr): New email address.
    """
    email: EmailStr


class UserSwitchType(BaseModel):
    """
    Schema for switching user service type.

    Attributes:
        user_type (UserType): New service type (prepaid/postpaid).
    """
    user_type: UserType


class UserDeactivate(BaseModel):
    """
    Schema for user account deactivation request.

    Attributes:
        reason (Optional[str]): Optional reason for deactivation.
    """
    reason: Optional[str] = None


class UserRegisterRequest(BaseModel):
    """
    Schema for user registration/onboarding request.

    Attributes:
        name (str): User's full name (2-50 characters).
        email (EmailStr): Valid email address.
        referee_code (Optional[str]): Optional referral code of referrer.
    """
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    user_type: Literal["prepaid", "postpaid"]
    referee_code: Optional[str] = None

class UserRegisterResponse(BaseModel):
    """
    Schema for user registration response with created user details.

    Attributes:
        user_id (int): Newly created user ID.
        name (str): User's full name.
        email (EmailStr): User's email address.
        phone_number (str): User's phone number.
        referral_code (Optional[str]): Generated referral code.
        referee_code (Optional[str]): Referrer's code.
        user_type (str): Service type (prepaid/postpaid).
        status (str): Initial account status.
        wallet_balance (float): Initial wallet balance.
    """
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
    """
    Base schema for user notification and communication preferences.

    Attributes:
        email_notification (bool): Enable email notifications (default: True).
        sms_notification (bool): Enable SMS notifications (default: True).
        marketing_communication (bool): Enable marketing emails (default: False).
        recharge_remainders (bool): Enable recharge reminders (default: True).
        promotional_offers (bool): Enable promotional offers (default: False).
        transactional_alerts (bool): Enable transaction alerts (default: True).
        data_analytics (bool): Allow analytics collection (default: True).
        third_party_integrations (bool): Allow third-party integrations (default: False).
    """
    email_notification: bool = True
    sms_notification: bool = True
    marketing_communication: bool = False
    recharge_remainders: bool = True
    promotional_offers: bool = False
    transactional_alerts: bool = True
    data_analytics: bool = True
    third_party_integrations: bool = False

class UserPreferenceUpdate(UserPreferenceBase):
    """
    Schema for updating user preferences (inherits all fields from UserPreferenceBase).
    """
    pass

class UserPreferenceResponse(UserPreferenceBase):
    """
    Schema for returning user preferences in responses.

    Inherits from UserPreferenceBase. Attributes:
        user_id (int): Associated user ID.
    """
    user_id: int

    class Config:
        from_attributes = True
