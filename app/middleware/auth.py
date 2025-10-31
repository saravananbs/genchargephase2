# middleware/auth.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from jose import jwt, JWTError
from ..crud.token_revocation import is_token_revoked
from ..core.database import AsyncSessionLocal
from ..core.config import settings


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/auth"):
            return await call_next(request)

        authorization: str | None = request.headers.get("Authorization")

        if not authorization:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing Authorization header"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid scheme")

            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            jti = payload.get("jti")
            if not jti:
                raise ValueError("Missing jti")

            async with AsyncSessionLocal() as db:
                if await is_token_revoked(db, jti):
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Token revoked"},
                        headers={"WWW-Authenticate": "Bearer"},
                    )

        except (ValueError, JWTError):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invaid token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)