# api/routes/auth/__init__.py
from fastapi import APIRouter, Depends
from ....dependencies.permissions import require_scopes
from ....dependencies.auth import get_current_user
from ....core.database import get_db
from ....services.auth import AuthService

router = APIRouter()

@router.get("/admin/stats", dependencies=[Depends(require_scopes(["Users:read"]))])
async def get_admin_dashboard(
    auth_service: AuthService = Depends(),
    db = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return {"message": "Admin dashboard data"}
