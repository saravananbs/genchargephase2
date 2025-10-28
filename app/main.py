# main.py
from fastapi import FastAPI
from .api.routes.auth import router as auth_router
from .core.database import engine
from .core.database import Base
from .middleware.auth import AuthMiddleware

app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])

# Add middlewares
app.add_middleware(AuthMiddleware)