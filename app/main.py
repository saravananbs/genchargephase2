# main.py
from fastapi import FastAPI
from .api.routes.auth import router as auth_router
from .api.routes.testing import router as testing_router
from .core.database import engine
from .core.database import Base
from .middleware.auth import AuthMiddleware
import asyncio
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

app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(testing_router, prefix="/test", tags=["test"])

# Add middlewares
# app.add_middleware(AuthMiddleware)



