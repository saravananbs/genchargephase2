from fastapi import APIRouter, Depends, HTTPException, Request, Response, Security
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ....core.database import get_db
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes
from ....models.users import User
from ....crud import users as crud_user
from ....services.user import update_preferences_service
from ....schemas.users import (
    UserResponse, UserListFilters,
    UserEditEmail, UserSwitchType, UserDeactivate, UserRegisterRequest, UserRegisterResponse,
    UserPreferenceUpdate, UserPreferenceResponse
)

router = APIRouter()

# ---------- ADMIN ROUTES ----------
@router.get("/admin", response_model=List[UserResponse])
async def list_users(
    request: Request,
    response: Response,
    filters: UserListFilters = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Users:read"], use_cache=False)
):
    users = await crud_user.get_users(db, filters)
    return users

@router.get("/admin/archived", response_model=List[UserResponse])
async def list_archived_users(
    request: Request,
    response: Response,
    filters: UserListFilters = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Users:read"], use_cache=False)
):
    archived = await crud_user.get_archived_users(db, filters)
    return archived

@router.post("/admin/block/{user_id}", response_model=UserResponse)
async def block_user(
    request: Request,
    response: Response,
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Users:edit"], use_cache=False)
):
    print(current_user.status)
    user = await crud_user.block_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/admin/unblock/{user_id}", response_model=UserResponse)
async def unblock_user(
    request: Request,
    response: Response,
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Users:edit"], use_cache=False)
):
    print(current_user.status)
    user = await crud_user.unblock_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/admin/{user_id}", response_model=UserResponse)
async def delete_user(
    request: Request,
    response: Response,
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Users:delete"], use_cache=False)
):
    deleted = await crud_user.delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted


# ---------- USER ROUTES ----------
@router.get("/me", response_model=UserResponse)
async def get_my_info(
    request: Request,
    response: Response,
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"], use_cache=False)
):
    return current_user

@router.put("/me/email", response_model=UserResponse)
async def update_email(
    request: Request,
    response: Response,
    data: UserEditEmail,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    authorized = Security(require_scopes, scopes=["User"], use_cache=False)
):
    updated = await crud_user.update_email(db, current_user.user_id, data.email)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated

@router.put("/me/switch-type", response_model=UserResponse)
async def switch_user_type(
    request: Request,
    response: Response,
    data: UserSwitchType,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    authorized = Security(require_scopes, scopes=["User"], use_cache=False)
):
    updated = await crud_user.switch_user_type(db, current_user.user_id, data.user_type)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated

@router.post("/me/deactivate", response_model=UserResponse)
async def deactivate_account(
    request: Request,
    response: Response,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    authorized = Security(require_scopes, scopes=["User"], use_cache=False)
):
    print(current_user.status)
    updated = await crud_user.deactivate_user(db, current_user.user_id)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated

@router.post("/me/reactivate", response_model=UserResponse)
async def reactivate_account(
    request: Request,
    response: Response,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    authorized = Security(require_scopes, scopes=["User"], use_cache=False)
):
    print(current_user.status)
    updated = await crud_user.reactivate_user(db, current_user.user_id)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated

@router.delete("/me", response_model=UserResponse)
async def delete_my_account(
    request: Request,
    response: Response,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    authorized = Security(require_scopes, scopes=["User"], use_cache=False)
):
    deleted = await crud_user.delete_user_account(db, current_user.user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted

@router.get("/preference", response_model=UserPreferenceResponse)
async def update_user_preferences(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"], use_cache=False)
):
    result = await crud_user.get_user_preference(db, current_user.user_id)
    return result

@router.put("/preference", response_model=UserPreferenceResponse)
async def update_user_preferences(
    data: UserPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"], use_cache=False)
):
    updated_pref = await update_preferences_service(db, current_user.user_id, data)
    return updated_pref

