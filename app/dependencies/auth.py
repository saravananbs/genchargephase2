# dependencies/auth.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt, ExpiredSignatureError
from sqlalchemy.orm import Session
from ..core.config import settings
from ..core.database import get_db
from ..crud.users import get_user_by_phone
from ..crud.admin import get_admin_by_phone
from ..crud.token_revocation import is_token_revoked
from ..schemas.auth import TokenData

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        phone: str = payload.get("sub")
        if phone is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        token_data = TokenData(phone_number=phone)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token at the authroization header")

    user = await get_user_by_phone(db, phone=token_data.phone_number)
    if not user:
        user = await get_admin_by_phone(db, phone=token_data.phone_number)
    flag = await is_token_revoked(db, payload.get("jti"))
    if user is None or flag:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return user

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    if current_user.status != "active":
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def role_required(required_role: str):
    async def role_checker(current_user: dict = Depends(get_current_active_user)):
        if current_user.role_id != required_role:  # Assuming role_id is string or adjust accordingly
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker
