from fastapi import APIRouter, Depends, HTTPException, Request, Response, Security
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ....core.database import get_db
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes
from ....models.users import User
from ....crud import users as crud_user
from ....services.user import update_preferences_service
from ....schemas.users import (
    UserResponse, UserListFilters,
    UserEditEmail, UserSwitchType, UserDeactivate, UserRegisterRequest, UserRegisterResponse,
    UserPreferenceUpdate, UserPreferenceResponse
)

router = APIRouter()

# ---------- ADMIN ROUTES ----------
@router.get("/admin", response_model=List[UserResponse])
async def list_users(
    request: Request,
    response: Response,
    filters: UserListFilters = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Users:read"])
):
    """
    Retrieve list of all active users with advanced filtering and pagination.
    
    Admin endpoint to retrieve all active (non-archived, non-deleted) users in the system.
    Supports extensive filtering by user type, status, creation date, email, phone, and more.
    Results can be sorted and paginated for better performance.
    
    Security:
        - Requires valid JWT access token
        - Scope: Users:read
        - Admin-only endpoint
    
    Query Parameters (UserListFilters):
        - user_type (str, optional): Filter by 'prepaid' or 'postpaid'
        - search (str, optional): Search by phone, email, or name (LIKE pattern)
        - is_active (bool, optional): Filter by active status
        - created_from (datetime, optional): Users created after this date
        - created_to (datetime, optional): Users created before this date
        - page (int): Page number for pagination (default: 1)
        - limit (int): Records per page (default: 10, max: 100)
        - sort_by (str): Sort field (default: 'user_id')
        - sort_order (str): 'asc' or 'desc' (default: 'desc')
    
    Returns:
        List[UserResponse]: Array of user objects with profile information.
        
    Raises:
        HTTPException(401): If not authenticated or invalid token.
        HTTPException(403): If user doesn't have Users:read scope.
    
    Example:
        Request:
        ```
        GET /users/admin?user_type=prepaid&is_active=true&page=1&limit=20
        Authorization: Bearer <admin_token>
        ```
        
        Response:
        ```json
        [
            {
                "user_id": 1,
                "phone": "+919876543210",
                "email": "user@example.com",
                "name": "Raj Kumar",
                "user_type": "prepaid",
                "is_active": true,
                "wallet_balance": 500.50,
                "created_at": "2024-01-15T10:30:00Z"
            }
        ]
        ```
    """
    users = await crud_user.get_users(db, filters)
    return users

@router.get("/admin/archived", response_model=List[UserResponse])
async def list_archived_users(
    request: Request,
    response: Response,
    filters: UserListFilters = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Users:read"])
):
    """
    Retrieve list of all archived/deleted users.
    
    Admin endpoint to retrieve users that have been deleted or archived from the system.
    These are users who deactivated their accounts or were removed by administrators.
    Supports the same filtering, sorting, and pagination options as active users.
    
    Security:
        - Requires valid JWT access token
        - Scope: Users:read
        - Admin-only endpoint
    
    Query Parameters (UserListFilters):
        - user_type (str, optional): Filter by 'prepaid' or 'postpaid'
        - search (str, optional): Search by phone, email, or name
        - created_from (datetime, optional): Users archived after this date
        - created_to (datetime, optional): Users archived before this date
        - page (int): Page number for pagination (default: 1)
        - limit (int): Records per page (default: 10)
        - sort_by (str): Sort field (default: 'user_id')
        - sort_order (str): 'asc' or 'desc'
    
    Returns:
        List[UserResponse]: Array of archived user objects.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing Users:read scope.
    
    Example:
        Request:
        ```
        GET /users/admin/archived?page=1&limit=50
        Authorization: Bearer <admin_token>
        ```
        
        Response:
        ```json
        [
            {
                "user_id": 100,
                "phone": "+919999999999",
                "name": "Deleted User",
                "is_active": false,
                "deleted_at": "2024-01-10T15:45:00Z"
            }
        ]
        ```
    """
    archived = await crud_user.get_archived_users(db, filters)
    return archived

@router.post("/admin/block/{user_id}", response_model=UserResponse)
async def block_user(
    request: Request,
    response: Response,
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Users:edit"])
):
    """
    Block a specific user account preventing their access to the platform.
    
    Admin endpoint to block a user permanently. Blocked users cannot login, make transactions,
    or perform any operations. Their account is marked as inactive. This action is useful for
    preventing fraudulent users or those violating terms of service from accessing the platform.
    
    Security:
        - Requires valid JWT access token
        - Scope: Users:edit
        - Admin-only endpoint
    
    Path Parameters:
        - user_id (int): Unique identifier of the user to block.
    
    Returns:
        UserResponse: Updated user object with is_active=false and block status.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing Users:edit scope.
        HTTPException(404): If user with specified ID not found.
    
    Example:
        Request:
        ```
        POST /users/admin/block/42
        Authorization: Bearer <admin_token>
        ```
        
        Response:
        ```json
        {
            "user_id": 42,
            "phone": "+919876543210",
            "name": "Blocked User",
            "is_active": false,
            "blocked_at": "2024-01-15T14:22:00Z",
            "block_reason": "Fraudulent activity"
        }
        ```
    """
    user = await crud_user.block_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/admin/unblock/{user_id}", response_model=UserResponse)
async def unblock_user(
    request: Request,
    response: Response,
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Users:edit"])
):
    """
    Unblock a previously blocked user account restoring access.
    
    Admin endpoint to unblock a user and restore their account access. Unblocked users
    can login and perform transactions again. This reverses a previous block action and
    is typically used after resolving issues or disputes with the user.
    
    Security:
        - Requires valid JWT access token
        - Scope: Users:edit
        - Admin-only endpoint
    
    Path Parameters:
        - user_id (int): Unique identifier of the user to unblock.
    
    Returns:
        UserResponse: Updated user object with is_active=true and block status removed.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing Users:edit scope.
        HTTPException(404): If user not found.
    
    Example:
        Request:
        ```
        POST /users/admin/unblock/42
        Authorization: Bearer <admin_token>
        ```
        
        Response:
        ```json
        {
            "user_id": 42,
            "phone": "+919876543210",
            "name": "User Name",
            "is_active": true,
            "unblocked_at": "2024-01-16T10:00:00Z"
        }
        ```
    """
    user = await crud_user.unblock_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/admin/{user_id}", response_model=UserResponse)
async def delete_user(
    request: Request,
    response: Response,
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Users:delete"])
):
    """
    Permanently delete a user account from the system.
    
    Admin endpoint to permanently delete a user account and all associated data.
    This is an irreversible operation that archives the user and marks them as deleted.
    Related data such as transactions may be retained for audit purposes but user
    personal information is marked as deleted. Use with caution.
    
    Security:
        - Requires valid JWT access token
        - Scope: Users:delete (elevated privilege)
        - Admin-only endpoint
        - Action is audited and logged
    
    Path Parameters:
        - user_id (int): Unique identifier of the user to delete.
    
    Returns:
        UserResponse: Deleted user object with deletion timestamp.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing Users:delete scope.
        HTTPException(404): If user not found.
    
    Example:
        Request:
        ```
        DELETE /users/admin/42
        Authorization: Bearer <admin_token_with_delete_scope>
        ```
        
        Response:
        ```json
        {
            "user_id": 42,
            "phone": "+919876543210",
            "is_active": false,
            "deleted_at": "2024-01-15T14:30:00Z",
            "deletion_reason": "User requested account deletion"
        }
        ```
    """
    deleted = await crud_user.delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted


# ---------- USER ROUTES ----------
@router.get("/me", response_model=UserResponse)
async def get_my_info(
    request: Request,
    response: Response,
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"])
):
    """
    Retrieve current user's profile information.
    
    User endpoint to get their own profile details including personal information,
    account status, wallet balance, and account creation date. This is the primary
    endpoint for users to view their profile information.
    
    Security:
        - Requires valid JWT access token
        - Scope: User (any authenticated user)
        - Returns only current user's data (no user_id parameter needed)
    
    Returns:
        UserResponse: Complete user profile object.
        
    Raises:
        HTTPException(401): If not authenticated or token expired.
        HTTPException(403): If missing User scope.
    
    Example:
        Request:
        ```
        GET /users/me
        Authorization: Bearer <access_token>
        ```
        
        Response:
        ```json
        {
            "user_id": 1,
            "phone": "+919876543210",
            "email": "user@example.com",
            "name": "Raj Kumar",
            "user_type": "prepaid",
            "is_active": true,
            "wallet_balance": 1250.75,
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-20T08:15:00Z"
        }
        ```
    """
    return current_user

@router.put("/me/email", response_model=UserResponse)
async def update_email(
    request: Request,
    response: Response,
    data: UserEditEmail,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    authorized = Security(require_scopes, scopes=["User"])
):
    """
    Update current user's email address.
    
    User endpoint to update their registered email address. The new email is validated
    for format and uniqueness. Email updates are typically used for account recovery,
    notifications, and support communications.
    
    Security:
        - Requires valid JWT access token
        - Scope: User
        - Can only update own email
    
    Request Body (UserEditEmail):
        - email (str): New email address (valid email format, must be unique in system)
    
    Returns:
        UserResponse: Updated user object with new email address.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing User scope.
        HTTPException(400): If email format invalid or already exists.
        HTTPException(404): If user not found.
    
    Example:
        Request:
        ```
        PUT /users/me/email
        Authorization: Bearer <access_token>
        Content-Type: application/json
        
        {
            "email": "newemail@example.com"
        }
        ```
        
        Response:
        ```json
        {
            "user_id": 1,
            "phone": "+919876543210",
            "email": "newemail@example.com",
            "name": "Raj Kumar",
            "updated_at": "2024-01-20T10:15:00Z"
        }
        ```
    """
    updated = await crud_user.update_email(db, current_user.user_id, data.email)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated

@router.put("/me/switch-type", response_model=UserResponse)
async def switch_user_type(
    request: Request,
    response: Response,
    data: UserSwitchType,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    authorized = Security(require_scopes, scopes=["User"])
):
    """
    Switch user account type between prepaid and postpaid.
    
    User endpoint to change their account type from prepaid to postpaid or vice versa.
    This affects billing model, subscription options, and available plans. The switch
    takes effect immediately and may impact ongoing subscriptions based on new plan
    availability.
    
    Security:
        - Requires valid JWT access token
        - Scope: User
        - Can only switch own account type
    
    Request Body (UserSwitchType):
        - user_type (str): Target user type - 'prepaid' or 'postpaid'
    
    Returns:
        UserResponse: Updated user object with new user_type.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing User scope.
        HTTPException(400): If invalid user_type or cannot switch (e.g., pending transactions).
        HTTPException(404): If user not found.
    
    Example:
        Request:
        ```
        PUT /users/me/switch-type
        Authorization: Bearer <access_token>
        Content-Type: application/json
        
        {
            "user_type": "postpaid"
        }
        ```
        
        Response:
        ```json
        {
            "user_id": 1,
            "phone": "+919876543210",
            "user_type": "postpaid",
            "switched_at": "2024-01-20T10:15:00Z"
        }
        ```
    """
    updated = await crud_user.switch_user_type(db, current_user.user_id, data.user_type)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated

@router.post("/me/deactivate", response_model=UserResponse)
async def deactivate_account(
    request: Request,
    response: Response,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    authorized = Security(require_scopes, scopes=["User"])
):
    """
    Deactivate current user account temporarily.
    
    User endpoint to deactivate their own account. Deactivated accounts cannot login or
    perform transactions but remain in the system and can be reactivated. This is useful
    for users wanting temporary breaks from the service without permanent deletion.
    
    Security:
        - Requires valid JWT access token
        - Scope: User
        - Can only deactivate own account
        - Current session is invalidated after deactivation
    
    Returns:
        UserResponse: Updated user object with is_active=false.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing User scope.
        HTTPException(400): If account already deactivated or has pending operations.
        HTTPException(404): If user not found.
    
    Example:
        Request:
        ```
        POST /users/me/deactivate
        Authorization: Bearer <access_token>
        ```
        
        Response:
        ```json
        {
            "user_id": 1,
            "phone": "+919876543210",
            "is_active": false,
            "deactivated_at": "2024-01-20T10:15:00Z",
            "message": "Account deactivated. You can reactivate anytime."
        }
        ```
    """
    updated = await crud_user.deactivate_user(db, current_user.user_id)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated

@router.post("/me/reactivate", response_model=UserResponse)
async def reactivate_account(
    request: Request,
    response: Response,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    authorized = Security(require_scopes, scopes=["User"])
):
    """
    Reactivate a deactivated user account.
    
    User endpoint to restore access to a previously deactivated account. Once reactivated,
    the user can login and perform transactions normally. This reverses the deactivation
    and restores full account functionality.
    
    Security:
        - Requires valid JWT access token
        - Scope: User
        - Can only reactivate own account
    
    Returns:
        UserResponse: Updated user object with is_active=true.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing User scope.
        HTTPException(400): If account is already active.
        HTTPException(404): If user not found.
    
    Example:
        Request:
        ```
        POST /users/me/reactivate
        Authorization: Bearer <access_token>
        ```
        
        Response:
        ```json
        {
            "user_id": 1,
            "phone": "+919876543210",
            "is_active": true,
            "reactivated_at": "2024-01-20T14:30:00Z",
            "message": "Account reactivated successfully"
        }
        ```
    """
    updated = await crud_user.reactivate_user(db, current_user.user_id)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated

@router.delete("/me", response_model=UserResponse)
async def delete_my_account(
    request: Request,
    response: Response,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    authorized = Security(require_scopes, scopes=["User"])
):
    """
    Permanently delete current user account.
    
    User endpoint to request permanent account deletion. This is an irreversible operation
    that archives the user's account and marks personal data as deleted. Transaction
    history and audit records are retained for compliance but user identifying information
    is removed. The user's current session is immediately terminated.
    
    Security:
        - Requires valid JWT access token
        - Scope: User
        - Can only delete own account
        - Irreversible operation (no recovery possible)
        - Action is logged for audit purposes
    
    Returns:
        UserResponse: Deleted user object with deletion timestamp.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing User scope.
        HTTPException(400): If account has pending transactions.
        HTTPException(404): If user not found.
    
    Example:
        Request:
        ```
        DELETE /users/me
        Authorization: Bearer <access_token>
        ```
        
        Response:
        ```json
        {
            "user_id": 1,
            "is_active": false,
            "deleted_at": "2024-01-20T15:45:00Z",
            "message": "Account permanently deleted. Your data has been removed from our systems."
        }
        ```
    """
    deleted = await crud_user.delete_user_account(db, current_user.user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted

@router.get("/preference", response_model=UserPreferenceResponse)
async def get_user_preferences(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"])
):
    """
    Retrieve current user's preference settings.
    
    User endpoint to fetch their account preferences and settings including notification
    preferences, communication preferences, privacy settings, and other personalization options.
    
    Security:
        - Requires valid JWT access token
        - Scope: User
        - Returns only current user's preferences
    
    Returns:
        UserPreferenceResponse: User's complete preference object with all settings.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing User scope.
        HTTPException(404): If preferences not found.
    
    Example:
        Request:
        ```
        GET /users/preference
        Authorization: Bearer <access_token>
        ```
        
        Response:
        ```json
        {
            "user_id": 1,
            "notifications_enabled": true,
            "email_notifications": true,
            "sms_notifications": true,
            "marketing_emails": false,
            "language": "en",
            "timezone": "Asia/Kolkata"
        }
        ```
    """
    result = await crud_user.get_user_preference(db, current_user.user_id)
    return result

@router.put("/preference", response_model=UserPreferenceResponse)
async def update_user_preferences(
    data: UserPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"])
):
    """
    Update current user's preference settings.
    
    User endpoint to modify account preferences and settings. Users can control notification
    settings, communication preferences, language, timezone, and other personalization options.
    Partial updates are supported - only provided fields are modified.
    
    Security:
        - Requires valid JWT access token
        - Scope: User
        - Can only update own preferences
    
    Request Body (UserPreferenceUpdate):
        - notifications_enabled (bool, optional): Enable/disable all notifications
        - email_notifications (bool, optional): Enable/disable email notifications
        - sms_notifications (bool, optional): Enable/disable SMS notifications
        - marketing_emails (bool, optional): Opt-in/out of marketing communications
        - language (str, optional): Preferred language code (en, hi, etc)
        - timezone (str, optional): Timezone identifier (Asia/Kolkata, etc)
    
    Returns:
        UserPreferenceResponse: Updated preference object with all current settings.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing User scope.
        HTTPException(400): If invalid preference values.
        HTTPException(404): If user not found.
    
    Example:
        Request:
        ```
        PUT /users/preference
        Authorization: Bearer <access_token>
        Content-Type: application/json
        
        {
            "notifications_enabled": false,
            "email_notifications": true,
            "language": "hi",
            "timezone": "Asia/Kolkata"
        }
        ```
        
        Response:
        ```json
        {
            "user_id": 1,
            "notifications_enabled": false,
            "email_notifications": true,
            "sms_notifications": true,
            "marketing_emails": false,
            "language": "hi",
            "timezone": "Asia/Kolkata",
            "updated_at": "2024-01-20T16:00:00Z"
        }
        ```
    """
    updated_pref = await update_preferences_service(db, current_user.user_id, data)
    return updated_pref

