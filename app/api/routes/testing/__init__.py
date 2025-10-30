from fastapi import APIRouter, Security, Depends
from ....dependencies.permissions import require_scopes
from ....dependencies.auth import get_current_user
from ....core.database import get_db
from ....services.auth import AuthService

router = APIRouter()

@router.get("/admin/stats")
async def get_admin_dashboard(
    auth_service: AuthService = Depends(),
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Users:read"])  # ✅ Using inbuilt scopes
):
    return {"message": "Admin dashboard data"}
