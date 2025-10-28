# api/routes/auth/__init__.py
from fastapi import APIRouter, Depends, Request
from ....schemas.auth import SignupRequest, OTPVerifyRequest, LoginRequest, LogoutRequest
from ....services.auth import AuthService
from ....schemas.auth import Token
from ....dependencies.auth import get_current_user

router = APIRouter()

@router.post("/signup")
async def signup(request: SignupRequest, auth_service: AuthService = Depends()):
    return await auth_service.signup(request)

@router.post("/verify-otp-signup")
async def verify_otp_signup(request: OTPVerifyRequest, auth_service: AuthService = Depends()):
    return await auth_service.verify_otp_signup(request)

@router.post("/login")
async def login(request: LoginRequest, auth_service: AuthService = Depends()):
    return await auth_service.login(request)

@router.post("/verify-otp-login")
async def verify_otp_login(request: OTPVerifyRequest, auth_service: AuthService = Depends()):
    return await auth_service.verify_otp_login(request)

@router.post("/logout")
async def logout(request: LogoutRequest, current_user: dict = Depends(get_current_user), auth_service: AuthService = Depends()):
    return await auth_service.logout(request, current_user)

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, current_user: dict = Depends(get_current_user), auth_service: AuthService = Depends()):
    return await auth_service.refresh_token(refresh_token, current_user)