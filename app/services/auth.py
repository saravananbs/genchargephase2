# services/auth.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from uuid import uuid4
from sqlalchemy import select
import datetime

from ..core.database import get_db
from ..crud.users import create_user, get_user_by_phone
from ..crud.admin import get_admin_by_phone, get_admin_role_by_phone
from ..crud.sessions import create_session, revoke_session, get_session_by_jti
from ..crud.token_revocation import revoke_token, is_token_revoked
from ..models.users import User
from ..models.admins import Admin
from ..models.sessions import Session as UserSession
from ..utils.otp import generate_otp, verify_otp, send_otp
from ..utils.security import create_access_token, create_refresh_token
from ..schemas.auth import SignupRequest, OTPVerifyRequest, LoginRequest, LogoutRequest, Token
from ..schemas.users import UserCreate
from ..core.config import settings


class AuthService:
    otp_store = {}

    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    # -------------------- USER SIGNUP -------------------- #
    async def signup(self, request: SignupRequest):
        """Signup only allowed for users, not admins"""
        user = await get_user_by_phone(self.db, request.phone_number)
        admin = await get_admin_by_phone(self.db, request.phone_number)

        if user or admin:
            raise HTTPException(status_code=400, detail="Account already exists")

        otp = '111111'
        self.__class__.otp_store[request.phone_number] = {
            "otp": otp,
            "expires_at": datetime.datetime.now() + datetime.timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
            "data": request.model_dump(),
            "identity_type": "user"
        }
        await send_otp(request.phone_number, otp)
        return {"message": f"OTP sent to {request.phone_number}"}

    async def verify_otp_signup(self, request: OTPVerifyRequest):
        """Verifies OTP and creates user"""
        key = request.phone_number
        stored = self.__class__.otp_store.get(key)
        if not stored or datetime.datetime.now() > stored["expires_at"]:
            raise HTTPException(status_code=400, detail="OTP expired or invalid")
        if not verify_otp(request.otp, stored["otp"]):
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # Create user
        user_data = UserCreate(**stored["data"])
        user = await create_user(self.db, user_data)

        # Create tokens
        jti = str(uuid4())
        access_token = create_access_token(data={"sub": request.phone_number, "role": "user"})
        refresh_token = create_refresh_token(data={"sub": request.phone_number, "jti": jti, "role": "user"})

        expires_at = datetime.datetime.now() + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await create_session(self.db, user.user_id, refresh_token, jti, expires_at)

        del self.otp_store[key]
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    # -------------------- COMMON LOGIN (USER + ADMIN) -------------------- #
    async def login(self, request: LoginRequest):
        """Both user and admin can login with phone number"""
        user = await get_user_by_phone(self.db, request.phone_number)
        admin = await get_admin_by_phone(self.db, request.phone_number)

        identity_type = None
        identity_id = None

        if user and str(user.status) == "UserStatus.active":
            identity_type = "user"
            identity_id = user.user_id
        elif admin and str(admin.status) == "AdminStatus.active":
            role = await get_admin_role_by_phone(self.db, request.phone_number)
            identity_type = role.role_name
            identity_id = admin.admin_id
        else:
            raise HTTPException(status_code=400, detail="Invalid or inactive account")

        otp = '111111'
        self.__class__.otp_store[request.phone_number] = {
            "otp": otp,
            "expires_at": datetime.datetime.now() + datetime.timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
            "identity_type": identity_type,
            "identity_id": identity_id
        }

        await send_otp(request.phone_number, otp)
        return {"message": f"OTP sent to {request.phone_number}"}

    async def verify_otp_login(self, request: OTPVerifyRequest):
        key = request.phone_number
        stored = self.__class__.otp_store.get(key)
        if not stored or datetime.datetime.now() > stored["expires_at"]:
            raise HTTPException(status_code=400, detail="OTP expired or invalid")
        if not verify_otp(request.otp, stored["otp"]):
            raise HTTPException(status_code=400, detail="Invalid OTP")

        identity_type = stored["identity_type"]
        identity_id = stored["identity_id"]

        # Retrieve model instance
        if identity_type == "user":
            result = await self.db.execute(select(User).filter(User.user_id == identity_id))
            entity = result.scalars().first()
        else:
            result = await self.db.execute(select(User).filter(User.user_id == identity_id))
            entity = result.scalars().first()
        jti = str(uuid4())
        access_token = create_access_token(data={"sub": entity.phone_number, "role": identity_type})
        refresh_token = create_refresh_token(data={"sub": entity.phone_number, "jti": jti, "role": identity_type})
        expires_at = datetime.datetime.now() + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        await create_session(self.db, identity_id, refresh_token, jti, expires_at)
        del self.otp_store[key]
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    # -------------------- LOGOUT -------------------- #
    async def logout(self, request: LogoutRequest, current_user):
        session = await self.db.query(UserSession).filter(UserSession.refresh_token == request.refresh_token).first()
        if not session:
            raise HTTPException(status_code=400, detail="Invalid refresh token")

        await revoke_session(self.db, session.session_id)
        refresh_payload = jwt.decode(request.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if refresh_payload['role'] == 'user':
            await revoke_token(self.db, session.jti, request.refresh_token, current_user.user_id, "logout", session.refresh_token_expires_at)
        else:
            await revoke_token(self.db, session.jti, request.refresh_token, current_user.admin_id, "logout", session.refresh_token_expires_at)
        return {"message": "Logged out"}

    # -------------------- REFRESH TOKEN -------------------- #
    async def refresh_token(self, refresh_token: str, current_user):
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            phone: str = payload.get("sub")
            jti: str = payload.get("jti")
            role: str = payload.get("role")
            print(payload)
            if not phone or not jti or not role:
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if await is_token_revoked(self.db, jti):
            raise HTTPException(status_code=401, detail="Refresh token revoked")

        session = await get_session_by_jti(self.db, jti)
        if not session or not session.is_active or session.refresh_token_expires_at < datetime.datetime.now():
            raise HTTPException(status_code=401, detail="Refresh token expired or invalid")

        if role == "user":
            entity = await get_user_by_phone(self.db, phone)
        else:
            entity = await get_admin_by_phone(self.db, phone)

        if not entity:
            raise HTTPException(status_code=401, detail="Account not found or inactive")


        new_access_token = create_access_token(data={"sub": phone, "role": role})
        new_jti = str(uuid4())
        new_refresh_token = create_refresh_token(data={"sub": phone, "jti": new_jti, "role": role})
        new_expires_at = datetime.datetime.now() + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        await revoke_token(self.db, session.jti, session.refresh_token, entity.admin_id if role == "admin" else entity.user_id, "token_refresh", session.refresh_token_expires_at)
        await revoke_session(self.db, session.session_id)
        await create_session(self.db, entity.admin_id if role == "admin" else entity.user_id, new_refresh_token, new_jti, new_expires_at)

        return Token(access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer")
