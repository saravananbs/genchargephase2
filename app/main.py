# main.py
from fastapi import FastAPI
from .api.routes.auth import router as auth_router
from .api.routes.testing import router as testing_router
from .api.routes.admin.admin_route import router as admin_router
from .api.routes.roles.role_router import router as role_router
from .core.database import engine
from .core.database import Base
from app.core.database import engine, Base
from contextlib import asynccontextmanager
from app.models import *

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup logic ---
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully.")

    yield 

    # --- Shutdown logic (optional) ---
    await engine.dispose()
    print("Database connection closed.")

app = FastAPI(title="GenCharge - A Moblie Recharge Application" , lifespan=lifespan)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(role_router, prefix="/role", tags=["role-permission"])




app.include_router(testing_router, prefix="/test", tags=["test"])




