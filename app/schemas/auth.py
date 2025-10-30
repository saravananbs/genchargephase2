# schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

class SignupRequest(BaseModel):
    phone_number: str
    user_type: str  # prepaid/postpaid

class OTPVerifyRequest(BaseModel):
    # email: Optional[EmailStr] = None
    username: str
    password: str

class LoginRequest(BaseModel):
    # email: Optional[EmailStr] = None
    phone_number: str

class LogoutRequest(BaseModel):
    refresh_token: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    phone_number: Optional[str] = None