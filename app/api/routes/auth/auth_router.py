from fastapi import APIRouter, Depends, Request, Response, Security
from fastapi.security import OAuth2PasswordRequestForm
from ....core.database import get_db
from ....schemas.users import UserRegisterResponse, UserRegisterRequest
from ....schemas.auth import SignupRequest, OTPVerifyRequest, LoginRequest, Token
from ....services.auth import AuthService
from ....models.users import User
from ....crud import users as crud_user
from ....dependencies.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from ....dependencies.permissions import require_scopes

router = APIRouter()

@router.post("/signup")
async def signup(request: SignupRequest, response: Response, auth_service: AuthService = Depends()):
    return await auth_service.signup(request, response)

@router.post("/verify-otp-signup")
async def verify_otp_signup(request: OTPVerifyRequest, response: Response, auth_service: AuthService = Depends()):
    return await auth_service.verify_otp_signup(request, response)

@router.post("/register", response_model=UserRegisterResponse)
async def register_user_route(
    data: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"], use_cache=False)
):
    user = await crud_user.register_user(db, current_user, data.name, data.email, data.referee_code)
    return user

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
