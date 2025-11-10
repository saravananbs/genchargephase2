from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from uuid import uuid4
import datetime
import json

from ..core.document_db import get_mongo_db
from ..crud.audit_logs import insert_audit_log
from ..core.database import get_db
from ..core.redis_client import get_redis
from ..crud.users import create_user, get_user_by_phone, get_user_by_id, create_user_preference
from ..crud.admin import get_admin_by_phone, get_admin_role_by_phone, get_admin_by_id
from ..crud.sessions import create_session, revoke_session, get_session_by_jti
from ..crud.token_revocation import revoke_token, is_token_revoked
from ..utils.otp import verify_otp, send_otp
from ..utils.security import create_access_token, create_refresh_token
from ..schemas.auth import SignupRequest, OTPVerifyRequest, LoginRequest, Token
from ..schemas.users import UserCreatenew
from ..core.config import settings


class AuthService:
    """
    Authentication service implementing signup, login, logout and token refresh flows.

    This service uses the application's relational DB (via AsyncSession), Redis for
    ephemeral OTP storage, and MongoDB for audit logs. It issues JWT access and
    refresh tokens using the configured secrets.
    """
    def __init__(self, db: AsyncSession = Depends(get_db)):
        """
        Initialize AuthService with a database session dependency.

        Args:
            db (AsyncSession): Async SQLAlchemy session injected by FastAPI.
        """
        self.db = db

    # -------------------- USER SIGNUP -------------------- #
    async def signup(self, request: SignupRequest, response: Response):
        """
        Start signup flow by storing OTP and user data in Redis and sending OTP.

        Args:
            request (SignupRequest): Signup payload containing phone_number and other user details.
            response (Response): FastAPI response object for setting cookies if needed.

        Returns:
            dict: A simple message indicating that the OTP was sent.

        Raises:
            HTTPException: 400 if the phone number is already associated with an account.
        """
        user = await get_user_by_phone(self.db, request.phone_number)
        admin = await get_admin_by_phone(self.db, request.phone_number)

        if user or admin:
            raise HTTPException(status_code=400, detail="Account already exists")

        otp = '111111'
        redis = await get_redis()

        data = {
            "otp": otp,
            "data": request.model_dump(),
            "identity_type": "user"
        }

        await redis.setex(
            f"otp:{request.phone_number}",
            settings.OTP_EXPIRE_MINUTES * 60,
            json.dumps(data)
        )

        await send_otp(request.phone_number, otp)
        return {"message": f"OTP sent to {request.phone_number}"}

    async def verify_otp_signup(self, req: OTPVerifyRequest, response: Response):
        """
        Verify OTP for signup, create the user, create session and return access token.

        Args:
            req (OTPVerifyRequest): Contains phone number and otp.
            response (Response): FastAPI response used to set the refresh token cookie.

        Returns:
            Token: Contains the issued access token.

        Raises:
            HTTPException: 400 when OTP is missing/invalid.
        """
        redis = await get_redis()
        stored_data = await redis.get(f"otp:{req.phone_number}")

        if not stored_data:
            raise HTTPException(status_code=400, detail="OTP expired or invalid")

        stored = json.loads(stored_data)
        if not verify_otp(req.otp, stored["otp"]):
            raise HTTPException(status_code=400, detail="Invalid OTP")

        user_data = UserCreatenew(**stored["data"])
        user = await create_user(self.db, user_data)
        await create_user_preference(self.db, user.user_id, {})

        jti = str(uuid4())
        access_token = create_access_token(data={"sub": req.phone_number, "jti": jti, "role": "user"})
        refresh_token = create_refresh_token(data={"sub": req.phone_number, "jti": jti, "role": "user"})

        expires_at = datetime.datetime.now() + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await create_session(self.db, user.user_id, refresh_token, jti, expires_at)

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=7 * 24 * 60 * 60
        )

        # Remove OTP entry from Redis
        await redis.delete(f"otp:{req.phone_number}")

        mongo_db = await get_mongo_db().__anext__()
        await insert_audit_log(
            db=mongo_db,
            action="User signup completed",
            service="auth_service",
            user_id=f"US_{user.user_id}",
            status="success"
        )

        return Token(access_token=access_token, refresh_token=None, token_type="bearer")

    # -------------------- LOGIN -------------------- #
    async def login(self, request: LoginRequest, response: Response):
        """
        Initiate login by determining identity type (user/admin), storing an OTP in Redis and sending it.

        Args:
            request (LoginRequest): Login request containing phone_number.
            response (Response): FastAPI response object.

        Returns:
            dict: Message indicating OTP was sent.

        Raises:
            HTTPException: 400 for invalid or inactive account.
        """
        user = await get_user_by_phone(self.db, request.phone_number)
        admin = await get_admin_by_phone(self.db, request.phone_number)

        identity_type, identity_id = None, None

        if user and str(user.status) == "UserStatus.deactive":
                identity_type = "user"
                identity_id = user.user_id
        elif user and str(user.status) == "UserStatus.active":
                identity_type = "user"
                identity_id = user.user_id
        elif admin:
            role = await get_admin_role_by_phone(self.db, request.phone_number)
            identity_type = role.role_name
            identity_id = admin.admin_id
        else:
            raise HTTPException(status_code=400, detail="Invalid or inactive account")

        otp = '111111'
        redis = await get_redis()

        data = {
            "otp": otp,
            "identity_type": identity_type,
            "identity_id": identity_id
        }

        await redis.setex(
            f"otp:{request.phone_number}",
            settings.OTP_EXPIRE_MINUTES * 60,
            json.dumps(data)
        )

        await send_otp(request.phone_number, otp)
        return {"message": f"OTP sent to {request.phone_number}"}

    async def verify_otp_login(self, req, response: Response):
        """
        Verify OTP for login and issue access/refresh tokens.

        The method supports both user and admin logins. It sets a secure refresh
        token cookie and records an audit log on successful login.

        Args:
            req: Request-like object holding `username` and `password` (OTP) fields.
            response (Response): FastAPI response to set the refresh cookie.

        Returns:
            Token: Issued access token.

        Raises:
            HTTPException: 400 when OTP is missing/invalid or account not found.
        """
        redis = await get_redis()
        stored_data = await redis.get(f"otp:{req.username}")

        if not stored_data:
            raise HTTPException(status_code=400, detail="OTP expired or invalid")

        stored = json.loads(stored_data)
        if not verify_otp(req.password, stored["otp"]):
            raise HTTPException(status_code=400, detail="Invalid OTP")

        identity_type = stored["identity_type"]
        identity_id = stored["identity_id"]

        if identity_type == "user":
            entity = await get_user_by_id(self.db, identity_id)
        else:
            entity = await get_admin_by_id(self.db, identity_id)

        jti = str(uuid4())
        access_token = create_access_token(data={"sub": entity.phone_number, "jti": jti, "role": identity_type})
        refresh_token = create_refresh_token(data={"sub": entity.phone_number, "jti": jti, "role": identity_type})
        expires_at = datetime.datetime.now() + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        await create_session(self.db, identity_id, refresh_token, jti, expires_at)
        await redis.delete(f"otp:{req.username}")

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=7 * 24 * 60 * 60
        )
        
        mongo_db = await get_mongo_db().__anext__()
        if identity_type == "user":
            user = await get_user_by_phone(self.db, req.username)
            if str(user.status) == "UserStatus.deactive":
                user.status = "active"
                self.db.add(user)
                await self.db.commit()
                await self.db.refresh(user)
            await insert_audit_log(
                db=mongo_db,
                action="User login successful",
                service="auth_service",
                user_id=f"US_{user.user_id}",
                status="success"
            )
        else:
            admin = await get_admin_by_phone(self.db, req.username)
            await insert_audit_log(
                db=mongo_db,
                action="Admin login successful",
                service="auth_service",
                user_id=f"AD_{admin.admin_id}",
                status="success"
            )

        return Token(access_token=access_token, refresh_token=None, token_type="bearer")

    # -------------------- LOGOUT -------------------- #
    async def logout(self, request: Request, response: Response, current_user):
        """
        Log out the current session by revoking the session and refresh token.

        Args:
            request (Request): Incoming request (used to read refresh token cookie).
            response (Response): Response object to delete cookies.
            current_user: The currently authenticated user/admin object.

        Returns:
            dict: Message confirming logout.

        Raises:
            HTTPException: 401 if refresh token cookie missing or invalid; 400 if session not found.
        """
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="No refresh token cookie found")

        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            jti = payload.get("jti")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        session = await get_session_by_jti(self.db, jti)
        if not session:
            raise HTTPException(status_code=400, detail="Session not found")

        role = payload.get('role')
        await revoke_session(self.db, session.session_id)
        if role == "user":
            await revoke_token(self.db, session.jti, refresh_token, current_user.user_id, "logout", session.refresh_token_expires_at)
        else:
            await revoke_token(self.db, session.jti, refresh_token, current_user.admin_id, "logout", session.refresh_token_expires_at)

        response.delete_cookie("refresh_token")
        mongo_db = await get_mongo_db().__anext__()
        if role == "user":
            await insert_audit_log(
                db=mongo_db,
                action="User logged out",
                service="auth_service",
                user_id=f"US_{current_user.user_id}",
                status="success"
            )
        else:
            await insert_audit_log(
                db=mongo_db,
                action="Admin logged out",
                service="auth_service",
                user_id=f"AD_{current_user.admin_id}",
                status="success"
            )
        return {"message": "Logged out successfully"}

    # -------------------- REFRESH TOKEN -------------------- #
    async def refresh_token(self, request: Request, response: Response):
        """
        Refresh access and refresh tokens using a valid refresh token cookie.

        This validates the refresh token, checks revocation and session validity,
        issues new tokens, and rotates the session record.

        Args:
            request (Request): Incoming request containing `refresh_token` cookie.
            response (Response): Response object used to set the new refresh cookie.

        Returns:
            Token: Newly issued access token.

        Raises:
            HTTPException: 401 for missing/invalid/revoked/expired refresh token or missing account.
        """
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Missing refresh token cookie")

        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            phone = payload.get("sub")
            jti = payload.get("jti")
            role = payload.get("role")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if await is_token_revoked(self.db, jti):
            raise HTTPException(status_code=401, detail="Refresh token revoked")

        session = await get_session_by_jti(self.db, jti)
        if not session or not session.is_active or session.refresh_token_expires_at < datetime.datetime.now():
            raise HTTPException(status_code=401, detail="Refresh token expired or invalid")

        entity = await (get_user_by_phone(self.db, phone) if role == "user" else get_admin_by_phone(self.db, phone))
        if not entity:
            raise HTTPException(status_code=401, detail="Account not found or inactive")

        new_jti = str(uuid4())
        new_access_token = create_access_token(data={"sub": phone, "jti": new_jti, "role": role})
        new_refresh_token = create_refresh_token(data={"sub": phone, "jti": new_jti, "role": role})
        new_expires_at = datetime.datetime.now() + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        await revoke_token(self.db, session.jti, session.refresh_token, entity.user_id if role == "user" else entity.admin_id, "token_refresh", session.refresh_token_expires_at)
        await revoke_session(self.db, session.session_id)
        await create_session(self.db, entity.user_id if role == "user" else entity.admin_id, new_refresh_token, new_jti, new_expires_at)

        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=7 * 24 * 60 * 60
        )
        mongo_db = await get_mongo_db().__anext__()
        if role == "user":
            user = await get_user_by_phone(self.db, phone)
            await insert_audit_log(
                db=mongo_db,
                action="User token refreshed",
                service="auth_service",
                user_id=f"US_{user.user_id}",
                status="success"
            )
        else:
            admin = await get_admin_by_phone(self.db, phone)
            await insert_audit_log(
                db=mongo_db,
                action="Admin token refreshed",
                service="auth_service",
                user_id=f"AD_{admin.admin_id}",
                status="success"
            )

        return Token(access_token=new_access_token, refresh_token=None, token_type="bearer")