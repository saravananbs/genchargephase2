# services/auth.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..crud.users import create_user, get_user_by_phone, update_user_status
from ..crud.sessions import create_session, revoke_session, get_session_by_jti
from ..crud.token_revocation import revoke_token, is_token_revoked
from ..utils.otp import generate_otp, verify_otp, send_otp  # Assume implementations
from ..utils.security import create_access_token, create_refresh_token
from ..schemas.auth import SignupRequest, OTPVerifyRequest, LoginRequest, LogoutRequest, Token
from ..schemas.users import UserCreate
from ..models.users import User
from ..models.sessions import Session as UserSession
import datetime
from uuid import uuid4
from ..core.config import settings
from jose import JWTError, jwt

class AuthService:
    otp_store = {}
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
          # Temporary in-memory for OTP, use Redis in production

    async def signup(self, request: SignupRequest):
        user = get_user_by_phone(self.db, request.phone_number)
        if user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        otp = '111111'
        self.__class__.otp_store[request.phone_number] = {
            "otp": otp,
            "expires_at": datetime.datetime.now() + datetime.timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
            "data": request.model_dump()
        }
        await send_otp(request.phone_number, otp)  # Implement send_otp
        print(self.__class__.otp_store)
        return {"message": f"OTP sent to {request.phone_number}"}

    async def verify_otp_signup(self, request: OTPVerifyRequest):
        key = request.phone_number
        stored = self.__class__.otp_store.get(key)
        if not stored or datetime.datetime.now() > stored["expires_at"]:
            raise HTTPException(status_code=400, detail="OTP expired or invalid")
        if not verify_otp(request.otp, stored["otp"]):
            raise HTTPException(status_code=400, detail="Invalid OTP")
        
        # Create the user
        user_data = UserCreate(**stored["data"])
        user = create_user(self.db, user_data)
    
        user = self.db.query(User).filter(User.user_id == stored["user_id"]).first()
        access_token = create_access_token(data={"sub": user.phone_number})
        jti = str(uuid4())
        refresh_token = create_refresh_token(data={"sub": user.phone_number, "jti": jti})
        expires_at = datetime.datetime.now() + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        create_session(self.db, user.user_id, refresh_token, jti, expires_at)
        del self.otp_store[key]
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


    async def login(self, request: LoginRequest):

        user = get_user_by_phone(self.db, request.phone_number)
        if not user or str(user.status) != "UserStatus.active":
            raise HTTPException(status_code=400, detail="Invalid user")
        
        otp = '111111'
        self.__class__.otp_store[request.phone_number] = {
            "otp": otp,
            "expires_at": datetime.datetime.now() + datetime.timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
            "user_id": user.user_id
        }
        await send_otp(request.phone_number, otp)
        return {"message": f"OTP sent to {request.phone_number}"}

    async def verify_otp_login(self, request: OTPVerifyRequest):
        key = request.phone_number
        stored = self.__class__.otp_store[key]
        if not stored or datetime.datetime.now() > stored["expires_at"]:
            raise HTTPException(status_code=400, detail="OTP expired or invalid")
        if not verify_otp(request.otp, stored["otp"]):
            raise HTTPException(status_code=400, detail="Invalid OTP")
        
        user = self.db.query(User).filter(User.user_id == stored["user_id"]).first()
        access_token = create_access_token(data={"sub": user.phone_number})
        jti = str(uuid4())
        refresh_token = create_refresh_token(data={"sub": user.phone_number, "jti": jti})
        expires_at = datetime.datetime.now() + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        create_session(self.db, user.user_id, refresh_token, jti, expires_at)
        del self.otp_store[key]
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    async def logout(self, request: LogoutRequest, current_user):
        # Find session by refresh_token
        session = self.db.query(UserSession).filter(UserSession.refresh_token == request.refresh_token).first()
        if not session:
            raise HTTPException(status_code=400, detail="Invalid refresh token")
        revoke_session(self.db, session.session_id)
        revoke_token(self.db, session.jti, request.refresh_token, current_user.user_id, "logout", session.refresh_token_expires_at)
        return {"message": "Logged out"}

    async def verify_otp_login(self, request: OTPVerifyRequest):
        key = request.phone_number
        stored = self.otp_store.get(key)
        if not stored or datetime.datetime.now() > stored["expires_at"]:
            raise HTTPException(status_code=400, detail="OTP expired or invalid")
        if not verify_otp(request.otp, stored["otp"]):
            raise HTTPException(status_code=400, detail="Invalid OTP")
        
        user = self.db.query(User).filter(User.user_id == stored["user_id"]).first()
        access_token = create_access_token(data={"sub": user.phone_number})
        jti = str(uuid4())
        refresh_token = create_refresh_token(data={"sub": user.phone_number, "jti": jti})
        expires_at = datetime.datetime.now() + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        create_session(self.db, user.user_id, refresh_token, jti, expires_at)
        del self.otp_store[key]
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    async def logout(self, request: LogoutRequest, current_user):
        session = self.db.query(UserSession).filter(UserSession.refresh_token == request.refresh_token).first()
        if not session:
            raise HTTPException(status_code=400, detail="Invalid refresh token")
        revoke_session(self.db, session.session_id)
        revoke_token(self.db, session.jti, request.refresh_token, current_user.user_id, "logout", session.refresh_token_expires_at)
        return {"message": "Logged out"}

    async def refresh_token(self, refresh_token: str, current_user):
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            phone: str = payload.get("sub")
            jti: str = payload.get("jti")
            if not phone or not jti:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        # Check if token is revoked
        if is_token_revoked(self.db, jti):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")
        # Check session validity
        session = get_session_by_jti(self.db, jti)
        if not session or not session.is_active or session.refresh_token_expires_at < datetime.datetime.now():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or invalid")

        # Get user
        user = get_user_by_phone(self.db, phone)
        if not user or str(user.status) != "UserStatus.active":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

        # Generate new access token
        new_access_token = create_access_token(data={"sub": user.phone_number})

        # Optionally, rotate refresh token for better security
        new_jti = str(uuid4())
        new_refresh_token = create_refresh_token(data={"sub": user.phone_number, "jti": new_jti})
        new_expires_at = datetime.datetime.now() + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        # Revoke old refresh token
        revoke_token(self.db, session.jti, session.refresh_token, user.user_id, "token_refresh", session.refresh_token_expires_at)
        revoke_session(self.db, session.session_id)

        # Create new session
        create_session(self.db, user.user_id, new_refresh_token, new_jti, new_expires_at)

        return Token(access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer")