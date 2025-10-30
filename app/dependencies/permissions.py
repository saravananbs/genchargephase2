from fastapi import Depends, HTTPException, status, Security
from fastapi.security import SecurityScopes
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..core.config import settings
from ..core.database import get_db
from ..crud.permissions import get_permissions_by_role
from .auth import oauth2_scheme

# ✅ OAuth2PasswordBearer handles both token retrieval and scope declarations


# ✅ Main permission dependency
async def require_scopes(
    security_scopes: SecurityScopes,
    token: str = Security(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    Verifies that the current user's role has all required scopes.
    Integrates with Swagger UI's OAuth2 authorize flow automatically.
    """
    authenticate_value = f'Bearer scope="{security_scopes.scope_str}"' if security_scopes.scopes else "Bearer"

    # ---------- Decode Token ----------
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        role_name = payload.get("role")
        if not role_name:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing role in token",
                headers={"WWW-Authenticate": authenticate_value},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": authenticate_value},
        )

    # ---------- Fetch Role Permissions ----------
    permissions = await get_permissions_by_role(db, role_name)
    if not permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permissions found for this role",
            headers={"WWW-Authenticate": authenticate_value},
        )
    # ---------- Build Allowed Scopes ----------
    available_scopes = set()
    for p in permissions:
        if p.read:
            available_scopes.add(f"{p.resource}:read")
        if p.write:
            available_scopes.add(f"{p.resource}:write")
        if p.edit:
            available_scopes.add(f"{p.resource}:edit")
        if p.delete:
            available_scopes.add(f"{p.resource}:delete")

    print(security_scopes.scopes)
    print(available_scopes)

    # ---------- Check Required Scopes ----------
    if not set(security_scopes.scopes).issubset(available_scopes):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not enough permissions. Required: {security_scopes.scopes}",
            headers={"WWW-Authenticate": authenticate_value},
        )

    return True  # ✅ Authorized