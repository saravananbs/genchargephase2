# middleware/auth.py
from fastapi import Request, HTTPException, middleware
from starlette.middleware.base import BaseHTTPMiddleware
from ..crud.token_revocation import is_token_revoked
from ..core.database import SessionLocal
from jose import jwt
from ..core.config import settings

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/auth"):
            return await call_next(request)
        
        authorization: str = request.headers.get("Authorization")
        if not authorization:
            response = await call_next(request)
            return response
            # raise HTTPException(status_code=401, detail="Invalid Header, Need authorization")  # Or raise exception if required
        
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise ValueError()
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            jti = payload.get("jti")
            db = SessionLocal()
            if is_token_revoked(db, jti):
                db.close()
                raise HTTPException(status_code=401, detail="Token revoked")
            db.close()
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return await call_next(request)