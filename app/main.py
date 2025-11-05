# main.py
from fastapi import FastAPI
from .api.routes.auth.auth_router import router as auth_router
from .api.routes.testing import router as testing_router
from .api.routes.admin.admin_router import router as admin_router
from .api.routes.roles.role_router import router as role_router
from .api.routes.users.users_router import router as user_router
from .api.routes.plans.plans_router import router as plans_router
from .api.routes.offers.offers_router import router as offer_router
from .api.routes.recharge.recharge_router import router as recharge_router
from .api.routes.autopay.autopay_router import router as autopay_router
from .api.routes.referrals.referrals_router import router as referrals_router
from .api.routes.contact_form.contact_form_router import router as contact_form_router
from .api.routes.content.content_router import router as content_router
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

    # --- Shutdown logic ---
    await engine.dispose()
    print("Database connection closed.")

app = FastAPI(title="GenCharge - A Moblie Recharge Application" , lifespan=lifespan)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(role_router, prefix="/role", tags=["role-permission"])
app.include_router(user_router, prefix="/user", tags=["user"])
app.include_router(plans_router, prefix="/plans", tags=["plans"])
app.include_router(offer_router, prefix="/offers", tags=["offers"])
app.include_router(recharge_router, prefix="/recharge", tags=["recharges"])
app.include_router(autopay_router, prefix="/autopay", tags=["autopay"])
app.include_router(referrals_router, prefix="/referrals", tags=["referrals"])
app.include_router(contact_form_router, prefix="/contact-from", tags=["contact-form"])
app.include_router(content_router, prefix="/content", tags=["content"])





app.include_router(testing_router, prefix="/test", tags=["test"])




