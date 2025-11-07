# main.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from .api.routes.auth.auth_router import router as auth_router
from .api.routes.testing import router as testing_router
from .api.routes.admin.admin_router import router as admin_router
from .api.routes.roles.role_router import router as role_router
from .api.routes.users.users_router import router as user_router
from .api.routes.plans.plans_router import router as plans_router
from .api.routes.offers.offers_router import router as offer_router
from .api.routes.recharge.recharge_router import router as recharge_router
from .api.routes.autopay.autopay_router import router as autopay_router
from .api.routes.notification.notification_router import router as notification_router
from .api.routes.referrals.referrals_router import router as referrals_router
from .api.routes.contact_form.contact_form_router import router as contact_form_router
from .api.routes.content.content_router import router as content_router
from .api.routes.backup.backup_router import router as backup_router
from .api.routes.reports.reports_router import router as reports_router
from .api.routes.analyticas.analytics_router import router as analytics_router
from .core.database import engine, Base
from .core.document_db import init_counters

from contextlib import asynccontextmanager
from app.models import *

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup logic ---
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully.")
    await init_counters()
    print("MongoDB notification_id counter initialized.")

    yield 

    # --- Shutdown logic ---
    await engine.dispose()
    print("Database connection closed.")

app = FastAPI(
    title="Gencharge",
    version="1.0.0",
    description="GenCharge - A Moblie Recharge Application",
    openapi_url="/openapi.json",
    docs_url=None,
    redoc_url="/redoc",
    lifespan=lifespan
)

@app.get("/docs", include_in_schema=False)
def custom_docs():
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
        <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
        <title>Custom Docs with Tag Filter</title>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>

        <script>
        const ui = SwaggerUIBundle({
            url: '/openapi.json',
            dom_id: '#swagger-ui',
            layout: 'BaseLayout',
            deepLinking: true,
            showExtensions: true,
            showCommonExtensions: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.SwaggerUIStandalonePreset
            ],
            onComplete: () => {
                // Wait for DOM to be ready
                const authButton = document.querySelector('.btn.authorize.unlocked');

  
    
    // Wait a short time in case the modal content loads dynamically
    setInterval(() => {
      
      const modal = document.querySelector('.modal-ux'); // or use your modal selector
modal.querySelectorAll('*').forEach(el => {
  el.childNodes.forEach(node => {
    if (node.nodeType === 3) {
      const text = node.textContent.trim();
      if (text.includes('username')) {
        node.textContent = text.replace(/username/gi, 'phone_number');
      }
      if (text.includes('password')) {
        node.textContent = text.replace(/password/gi, 'otp');
      }
    }  
  });
});
    }, 1000);
                setTimeout(() => {
                    const authWrapper = document.querySelector('.auth-wrapper');
                    if (authWrapper) {
                        const dropdown = document.createElement('select');
                        dropdown.style.marginRight = '10px';
                        dropdown.innerHTML = `
                            <option value="">-- Show All --</option>
                            <option value="Admin">Admin</option>
                            <option value="Analytics">Analytics</option>
                            <option value="Auth">Auth</option>
                            <option value="Autopay">Autopay</option>
                            <option value="Backup">Backup</option>
                            <option value="Contact-Form">Contact-Form</option>
                            <option value="Content">Content</option>
                            <option value="Notification">Notification</option>
                            <option value="Offers">Offers</option>
                            <option value="Plans">Plans</option>
                            <option value="Recharge">Recharge</option>
                            <option value="Referrals">Referrals</option>
                            <option value="Reports">Reports</option>
                            <option value="Roles">Roles</option>
                            <option value="Testing">Testing</option>
                            <option value="Users">Users</option>
                        `;

                        
                        dropdown.style.zIndex = '9999';
                        dropdown.style.padding = '8px';
                        dropdown.style.backgroundColor = '#f5f5f5';
                        dropdown.style.border = '1px solid #ccc';
                        dropdown.style.borderRadius = '4px';
                        dropdown.style.cursor = 'pointer';
                        dropdown.style.marginRight = '10px';


                        dropdown.onchange = function() {
                            const tag = this.value;
                            document.querySelectorAll('.opblock-tag-section').forEach(sec => {
                                const tagName = sec.querySelector('.opblock-tag').textContent.trim();
                                if (!tag || tagName === tag) {
                                    sec.style.display = '';
                                } else {
                                    sec.style.display = 'none';
                                }
                            });
                        };

                        // Insert dropdown before the auth button
                        authWrapper.parentNode.insertBefore(dropdown, authWrapper);
                    }
                }, 100); // Small delay to ensure Swagger UI renders
            }
        });
        </script>
    </body>
    </html>
'''
    return HTMLResponse(content=html)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(role_router, prefix="/role", tags=["Roles"])
app.include_router(user_router, prefix="/user", tags=["Users"])
app.include_router(plans_router, prefix="/plans", tags=["Plans"])
app.include_router(offer_router, prefix="/offers", tags=["Offers"])
app.include_router(recharge_router, prefix="/recharge", tags=["Recharge"])
app.include_router(autopay_router, prefix="/autopay", tags=["Autopay"])
app.include_router(referrals_router, prefix="/referrals", tags=["Referrals"])
app.include_router(notification_router, prefix="/notification", tags=["Notification"])
app.include_router(contact_form_router, prefix="/contact-from", tags=["Contact-Form"])
app.include_router(content_router, prefix="/content", tags=["Content"])
app.include_router(backup_router, prefix="/backup", tags=["Backup"])
app.include_router(reports_router, prefix="/reports", tags=["Reports"])
app.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])







app.include_router(testing_router, prefix="/test", tags=["Testing"])




