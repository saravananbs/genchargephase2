# schemas/users.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: str
    referral_code: Optional[str] = None
    referred_by: Optional[str] = None
    user_type: str
    status: str = "active"
    wallet_balance: float = 0.0

class UserCreate(UserBase):
    created_at: datetime = datetime.now()
