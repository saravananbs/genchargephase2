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
    """
    Initiate user signup with phone number.
    
    This endpoint starts the signup process by registering a phone number and triggering
    OTP generation for verification. The OTP is sent via SMS to the provided phone number.
    The user must verify the OTP using the verify-otp-signup endpoint.
    
    Args:
        request (SignupRequest): Request body containing phone number in international format.
        response (Response): Response object to set cookies.
        auth_service (AuthService): Authentication service dependency.
    
    Returns:
        dict: Response containing OTP timer, phone number, and next steps information.
        
    Raises:
        HTTPException(400): If phone number is invalid or already registered.
        HTTPException(429): If too many signup attempts from the same phone.
    
    Example:
        Request:
        ```json
        {
            "phone": "+919876543210"
        }
        ```
        
        Response:
        ```json
        {
            "message": "OTP sent successfully",
            "phone": "+919876543210",
            "otp_timer_seconds": 300,
            "next_endpoint": "/auth/verify-otp-signup"
        }
        ```
    """
    return await auth_service.signup(request, response)

@router.post("/verify-otp-signup")
async def verify_otp_signup(request: OTPVerifyRequest, response: Response, auth_service: AuthService = Depends()):
    """
    Verify OTP received during signup process.
    
    Verifies the OTP sent to the user's phone number during signup. Upon successful verification,
    the user account is created and authentication tokens (access_token, refresh_token) are returned
    via HTTP-only cookies. The response includes the user's basic profile information.
    
    Args:
        request (OTPVerifyRequest): Request body containing phone number and OTP code.
        response (Response): Response object to set authentication cookies.
        auth_service (AuthService): Authentication service dependency.
    
    Returns:
        dict: Response containing user profile, access token, and token expiry information.
        
    Raises:
        HTTPException(400): If phone number is not found or OTP is invalid.
        HTTPException(401): If OTP has expired or too many verification attempts.
        HTTPException(409): If user already exists with the same phone number.
    
    Example:
        Request:
        ```json
        {
            "phone": "+919876543210",
            "otp": "123456"
        }
        ```
        
        Response:
        ```json
        {
            "user": {
                "user_id": 1,
                "phone": "+919876543210",
                "user_type": "prepaid",
                "is_active": true,
                "created_at": "2024-01-15T10:30:00Z"
            },
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "token_type": "bearer",
            "expires_in": 60
        }
        ```
    """
    return await auth_service.verify_otp_signup(request, response)

@router.post("/register", response_model=UserRegisterResponse)
async def register_user_route(
    data: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"])
):
    """
    Register a guest/provisional user with profile details.
    
    Converts a guest user or provisional account into a fully registered user by adding
    profile information (name, email) and optional referral code. Only authenticated users
    with "User" scope can register themselves. This endpoint completes the user onboarding process.
    
    Security:
        - Requires valid JWT access token
        - Scope: User
        - User can only register themselves (current_user)
    
    Args:
        data (UserRegisterRequest): Request body with name, email, and optional referee_code.
        db (AsyncSession): Database session dependency.
        current_user (User): Currently authenticated user object.
        authorized: OAuth2 scope authorization dependency.
    
    Returns:
        UserRegisterResponse: Registered user profile with all details (id, phone, name, email, etc).
        
    Raises:
        HTTPException(401): If not authenticated or invalid token.
        HTTPException(403): If user doesn't have required scope.
        HTTPException(400): If email already exists or invalid referee code.
        HTTPException(404): If current user not found.
    
    Example:
        Request Headers:
        ```
        Authorization: Bearer <access_token>
        ```
        
        Request Body:
        ```json
        {
            "name": "Raj Kumar",
            "email": "raj@example.com",
            "referee_code": "REF123456"
        }
        ```
        
        Response:
        ```json
        {
            "user_id": 1,
            "phone": "+919876543210",
            "name": "Raj Kumar",
            "email": "raj@example.com",
            "user_type": "prepaid",
            "is_active": true,
            "created_at": "2024-01-15T10:30:00Z"
        }
        ```
    """
    user = await crud_user.register_user(db, current_user, data.name, data.email, data.referee_code)
    return user

@router.post("/login")
async def login(request: LoginRequest, response: Response, auth_service: AuthService = Depends()):
    """
    Initiate user login with phone number.
    
    Starts the login process for an existing user by sending an OTP to their registered phone number.
    The user must verify the OTP using the verify-otp-login endpoint. This is the first step of
    the two-factor authentication login flow.
    
    Args:
        request (LoginRequest): Request body containing registered phone number.
        response (Response): Response object to set cookies.
        auth_service (AuthService): Authentication service dependency.
    
    Returns:
        dict: Response containing OTP timer, phone number, and next steps.
        
    Raises:
        HTTPException(400): If phone number format is invalid.
        HTTPException(404): If user with provided phone number doesn't exist.
        HTTPException(429): If too many login attempts from the same phone.
    
    Example:
        Request:
        ```json
        {
            "phone": "+919876543210"
        }
        ```
        
        Response:
        ```json
        {
            "message": "OTP sent to your phone",
            "phone": "+919876543210",
            "otp_timer_seconds": 300,
            "next_endpoint": "/auth/verify-otp-login"
        }
        ```
    """
    return await auth_service.login(request, response)

@router.post("/verify-otp-login")
async def verify_otp_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    response: Response = None,
    auth_service: AuthService = Depends()
):
    """
    Verify OTP received during login process.
    
    Completes the login process by verifying the OTP sent to the user's phone. Upon successful
    verification, access and refresh tokens are generated and set as HTTP-only cookies. This
    implements the second step of two-factor authentication (OTP-based).
    
    Args:
        form_data (OAuth2PasswordRequestForm): OAuth2 form containing username (phone) and password (OTP).
        response (Response): Response object to set authentication cookies.
        auth_service (AuthService): Authentication service dependency.
    
    Returns:
        Token: Response containing access_token, refresh_token, token_type, and expiry information.
        
    Raises:
        HTTPException(400): If phone number format is invalid.
        HTTPException(401): If OTP is incorrect or expired.
        HTTPException(404): If user with provided phone doesn't exist.
        HTTPException(403): If user account is blocked or deactivated.
    
    OAuth2 Parameters (via form_data):
        - username: Phone number in international format (e.g., +919876543210)
        - password: OTP code received via SMS (6 digits)
    
    Example:
        Form Data (application/x-www-form-urlencoded):
        ```
        username=+919876543210&password=123456
        ```
        
        Response:
        ```json
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 60,
            "user": {
                "user_id": 1,
                "phone": "+919876543210",
                "user_type": "prepaid"
            }
        }
        ```
    """
    return await auth_service.verify_otp_login(form_data, response)

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends()
):
    """
    Logout the currently authenticated user.
    
    Terminates the user's session by invalidating tokens, clearing cookies, and revoking
    the current access token in the token revocation list. The user's refresh token is also
    invalidated to prevent token reuse. This securely ends the user's authentication session.
    
    Security:
        - Requires valid JWT access token
        - Automatically invalidates current session
        - Prevents token replay attacks
    
    Args:
        request (Request): HTTP request object.
        response (Response): Response object to clear authentication cookies.
        current_user (dict): Currently authenticated user object.
        auth_service (AuthService): Authentication service dependency.
    
    Returns:
        dict: Logout confirmation message with success status.
        
    Raises:
        HTTPException(401): If not authenticated or invalid token.
    
    Example:
        Request Headers:
        ```
        Authorization: Bearer <access_token>
        ```
        
        Response:
        ```json
        {
            "message": "Logged out successfully",
            "status": "success"
        }
        ```
    """
    return await auth_service.logout(request, response, current_user)

@router.post("/refresh", response_model=Token)
async def refresh_token(request: Request, response: Response, auth_service: AuthService = Depends()):
    """
    Refresh expired access token using refresh token.
    
    Generates a new access token using the stored refresh token from HTTP-only cookies.
    This endpoint allows users to maintain their session without re-authenticating via OTP.
    The new access token is returned with a new expiration time (1 minute). Requires a valid
    refresh token that hasn't expired (valid for 2 days).
    
    Security:
        - Requires valid refresh token in HTTP-only cookie
        - Access token expiry: 1 minute
        - Refresh token expiry: 2 days
        - Automatic token rotation if refresh limit exceeded
    
    Args:
        request (Request): HTTP request object containing refresh token cookie.
        response (Response): Response object to set new access token cookie.
        auth_service (AuthService): Authentication service dependency.
    
    Returns:
        Token: New access_token with updated expiry time and user information.
        
    Raises:
        HTTPException(401): If refresh token is missing or invalid.
        HTTPException(403): If refresh token has expired or been revoked.
        HTTPException(400): If too many refresh attempts detected.
    
    Example:
        Request Headers:
        ```
        Cookie: refresh_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        ```
        
        Response:
        ```json
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 60,
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "user": {
                "user_id": 1,
                "phone": "+919876543210"
            }
        }
        ```
    """
    return await auth_service.refresh_token(request, response)
