# schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
import uuid


class SignupRequest(BaseModel):
    phone_number: str
    user_type: Literal["prepaid", "postpaid"]


class OTPVerifyRequest(BaseModel):
    phone_number: str
    otp: str

class LoginRequest(BaseModel):
    phone_number: str

class LogoutRequest(BaseModel):
    refresh_token: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str

class TokenData(BaseModel):
    phone_number: Optional[str] = None