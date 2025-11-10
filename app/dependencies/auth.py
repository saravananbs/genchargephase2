# dependencies/auth.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt, ExpiredSignatureError
from ..core.config import settings
from ..core.database import get_db
from ..crud.users import get_user_by_phone
from ..crud.admin import get_admin_by_phone
from ..crud.token_revocation import is_token_revoked
from ..schemas.auth import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/verify-otp-login",
                                     scopes={
                                            "Users:read": "Read user data",
                                            "Users:write": "Modify user data",
                                            "Users:delete": "Delete user data",
                                            "Admin:read": "Access admin dashboard",
                                            "Admin_me:edit": "Edit own profile",
                                            "Admins:edit": "Allows to edit all the admin"
                                            },
                                    )

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Extract and validate JWT token to retrieve current authenticated user.

    Decodes JWT token, verifies signature, checks token expiration, and confirms token is not revoked.
    Returns either a User or Admin object based on phone number claim.

    Args:
        token (str): JWT token from Authorization header (via oauth2_scheme).
        db (AsyncSession): Database session dependency.

    Returns:
        User or Admin: The authenticated user/admin object.

    Raises:
        HTTPException: 401 if token invalid, expired, or revoked.
        HTTPException: 401 if user/admin not found.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        phone: str = payload.get("sub")

        if phone is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        token_data = TokenData(phone_number=phone)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token at the authorization header"
        )

    user = await get_user_by_phone(db, phone=token_data.phone_number)
    if not user:
        user = await get_admin_by_phone(db, phone=token_data.phone_number)

    flag = await is_token_revoked(db, payload.get("jti"))
    if user is None or flag:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return user

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    """
    Verify that current authenticated user has active status.

    Dependency that checks if user's status is active, rejecting inactive users.

    Args:
        current_user (dict): Current user object from get_current_user dependency.

    Returns:
        dict: The active user object.

    Raises:
        HTTPException: 400 if user status is not active.
    """
    if status in current_user:
        if current_user.status != "active":
            raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def role_required(required_role: str):
    """
    Create a dependency for role-based access control (RBAC).

    Returns a closure that checks if current user's role matches the required role.

    Args:
        required_role (str): The required role_id for authorization.

    Returns:
        Callable: Async function to be used as a dependency that validates role.

    Raises:
        HTTPException: 403 if user does not have the required role.
    """
    async def role_checker(current_user: dict = Depends(get_current_active_user)):
        if current_user.role_id != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker
