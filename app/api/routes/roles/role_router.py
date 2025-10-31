# api/routes/roles.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ....core.database import get_db
from ....schemas.role import RoleCreate, RoleUpdate, RoleResponse, PermissionBase
from ....crud import role as crud_roles

router = APIRouter()

# ---------- List all roles ----------
@router.get("/", response_model=List[RoleResponse])
async def list_roles(db: AsyncSession = Depends(get_db)):
    roles = await crud_roles.get_all_roles(db)
    return [
        {
            "role_id": role.role_id,
            "role_name": role.role_name,
            "permissions": [
                {
                    "permission_id": rp.permission.permission_id,
                    "resource": rp.permission.resource,
                    "read": rp.permission.read,
                    "write": rp.permission.write,
                    "delete": rp.permission.delete,
                    "edit": rp.permission.edit,
                }
                for rp in role.role_permissions
            ],
        }
        for role in roles
    ]

# ---------- Get a single role ----------
@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(role_id: int, db: AsyncSession = Depends(get_db)):
    role = await crud_roles.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return {
            "role_id": role.role_id,
            "role_name": role.role_name,
            "permissions": [
                {
                    "permission_id": rp.permission.permission_id,
                    "resource": rp.permission.resource,
                    "read": rp.permission.read,
                    "write": rp.permission.write,
                    "delete": rp.permission.delete,
                    "edit": rp.permission.edit,
                }
                for rp in role.role_permissions
            ],
        }
        

# ---------- Create role ----------
@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(role_data: RoleCreate, db: AsyncSession = Depends(get_db)):
    role = await crud_roles.create_role(db, role_data.role_name, role_data.permission_ids)
    return {
            "role_id": role.role_id,
            "role_name": role.role_name,
            "permissions": [
                {
                    "permission_id": rp.permission_id,
                    "resource": rp.permission.resource,
                    "read": rp.permission.read,
                    "write": rp.permission.write,
                    "delete": rp.permission.delete,
                    "edit": rp.permission.edit,
                }
                for rp in role.role_permissions
            ],
        }

# ---------- Update role ----------
@router.put("/{role_id}", response_model=RoleResponse)
async def update_role_endpoint(
    role_id: int,
    role_data: RoleUpdate,
    db: AsyncSession = Depends(get_db)
):
    role = await crud_roles.update_role(
        db, role_id, role_data.role_name, role_data.permission_ids
    )
    return {
        "role_id": role.role_id,
        "role_name": role.role_name,
        "permissions": [
            {
                "permission_id": rp.permission.permission_id,
                "resource": rp.permission.resource,
                "read": rp.permission.read,
                "write": rp.permission.write,
                "delete": rp.permission.delete,
                "edit": rp.permission.edit,
            }
            for rp in role.role_permissions
        ],
    }

# ---------- Delete role ----------
@router.delete("/{role_id}")
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db)):
    return await crud_roles.delete_role(db, role_id)

# ---------- List all permissions ----------
@router.get("/permissions/all", response_model=List[PermissionBase])
async def list_permissions(db: AsyncSession = Depends(get_db)):
    permissions = await crud_roles.get_all_permissions(db)
    return permissions
