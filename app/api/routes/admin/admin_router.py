from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.ext.asyncio import AsyncSession
from ....core.database import get_db
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes
from ....schemas.admin import AdminCreate, AdminUpdate, AdminOut, AdminSelfUpdate
from ....crud import admin as admin_crud
from typing import List

router = APIRouter()

# ✅ GET /admins — List all admins
@router.get("/", response_model=List[AdminOut])
async def list_admins(
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Admins:read"], use_cache=False)
):
    admins = await admin_crud.get_admins(db)
    return [AdminOut.model_validate(admin, from_attributes=True) for admin in admins]


# ✅ POST /admins — Create a new admin
@router.post("/", response_model=AdminOut)
async def create_admin(
    admin_data: AdminCreate,
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Admins:write"], use_cache=False)
):
    return await admin_crud.create_admin(db, admin_data)


# ✅ DELETE /admins/{phone_number} — Delete an admin
@router.delete("/{phone_number}")
async def delete_admin(
    phone_number: str,
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Admins:delete"], use_cache=False)
):
    return await admin_crud.delete_admin_by_phone(db, phone_number)


# ✅ PATCH /admins/{phone_number} — Update admin info and role
@router.patch("/{phone_number}", response_model=AdminOut)
async def update_admin_by_phone(
    phone_number: str,
    data: AdminUpdate,
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Admins:edit"], use_cache=False)
):
    admin = await admin_crud.get_admin_by_phone(db, phone_number)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    updated_admin = await admin_crud.update_admin_by_phone(db, phone_number, data)
    return updated_admin


# ✅ GET /admin — Get current logged-in admin details
@router.get("/me", response_model=AdminOut)
async def get_self_admin(
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Admin_me:read"], use_cache=False)
):
    admin = await admin_crud.get_admin_by_id(db, current_user.admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin


# ✅ PATCH /admin — Update self (without role or phone change)
@router.patch("/by_phone/me", response_model=AdminOut)
async def update_self_admin(
    data: AdminSelfUpdate,
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Admin_me:edit"], use_cache=False)
):

    updated_admin = await admin_crud.update_admin(db, current_user.admin_id, data)
    return updated_admin
