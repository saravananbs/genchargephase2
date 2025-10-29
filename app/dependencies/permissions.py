# dependencies/permissions.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..core.config import settings
from ..core.database import get_db
from ..crud.permissions import get_permissions_by_role

security = HTTPBearer()

def require_scopes(required_scopes: List[str]):
    async def wrapper(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
    ):
        token = credentials.credentials

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            role_name = payload.get("role")
            if not role_name:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing role in token")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

        # Fetch permissions for this role (await if async)
        permissions = await get_permissions_by_role(db, role_name)
        if not permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permissions found for this role")

        # Build scope set
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

        # Verify scopes
        if not set(required_scopes).issubset(available_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions to access this resource. Required: {required_scopes}"
            )

        return True  # ✅ Authorized

    return wrapper
