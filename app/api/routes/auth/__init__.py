from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from ....schemas.auth import SignupRequest, OTPVerifyRequest, LoginRequest
from ....services.auth import AuthService
from ....schemas.auth import Token
from ....dependencies.auth import get_current_user

router = APIRouter()


@router.post("/signup")
async def signup(request: SignupRequest, response: Response, auth_service: AuthService = Depends()):
    return await auth_service.signup(request, response)


@router.post("/verify-otp-signup")
async def verify_otp_signup(request: OTPVerifyRequest, response: Response, auth_service: AuthService = Depends()):
    return await auth_service.verify_otp_signup(request, response)


@router.post("/login")
async def login(request: LoginRequest, response: Response, auth_service: AuthService = Depends()):
    return await auth_service.login(request, response)


@router.post("/verify-otp-login")
async def verify_otp_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    response: Response = None,
    auth_service: AuthService = Depends()
):
    return await auth_service.verify_otp_login(form_data, response)


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends()
):
    print(current_user)
    return await auth_service.logout(request, response, current_user)


@router.post("/refresh", response_model=Token)
async def refresh_token(request: Request, response: Response, auth_service: AuthService = Depends()):
    return await auth_service.refresh_token(request, response)
