# schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
import uuid


class SignupRequest(BaseModel):
    """
    Schema for user signup request.

    Attributes:
        phone_number (str): Phone number for the new user account.
        user_type (Literal): Service type - "prepaid" or "postpaid".
    """
    phone_number: str


class OTPVerifyRequest(BaseModel):
    """
    Schema for OTP verification during authentication.

    Attributes:
        phone_number (str): Phone number being verified.
        otp (str): One-time password sent to the phone.
    """
    phone_number: str
    otp: str

class LoginRequest(BaseModel):
    """
    Schema for user login request.

    Attributes:
        phone_number (str): Phone number of the user logging in.
    """
    phone_number: str

class LogoutRequest(BaseModel):
    """
    Schema for user logout request.

    Attributes:
        refresh_token (str): Refresh token to revoke upon logout.
    """
    refresh_token: str

class RefreshTokenRequest(BaseModel):
    """
    Schema for refreshing authentication tokens.

    Attributes:
        refresh_token (str): Refresh token to exchange for new access token.
    """
    refresh_token: str

class Token(BaseModel):
    """
    Schema for authentication token response.

    Attributes:
        access_token (str): JWT access token for API requests.
        refresh_token (Optional[str]): JWT refresh token for obtaining new access tokens.
        token_type (str): Type of token (typically "bearer").
    """
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str

class TokenData(BaseModel):
    """
    Schema for token claims/payload data.

    Attributes:
        phone_number (Optional[str]): Phone number from token claims.
    """
    phone_number: Optional[str] = None