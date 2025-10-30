# crud/permissions.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.roles import Role
from ..models.permissions import Permission
from ..schemas.permissions import PermissionCreate, PermissionUpdate
from ..models.roles_permissions import RolePermission

async def get_permissions_by_role(db: AsyncSession, role_name: str):
    """
    Fetch all permissions available for a given role name.
    Returns a list of Permission objects.
    """
    stmt = (
        select(Permission)
        .join(RolePermission, Permission.permission_id == RolePermission.permission_id)
        .join(Role, Role.role_id == RolePermission.role_id)
        .where(Role.role_name == role_name)
    )

    result = await db.execute(stmt)
    return result.scalars().all()

from sqlalchemy.future import select

async def get_permissions(db: AsyncSession):
    result = await db.execute(select(Permission))
    return result.scalars().all()

async def get_permission_by_id(db: AsyncSession, permission_id: int):
    result = await db.execute(select(Permission).where(Permission.permission_id == permission_id))
    return result.scalar_one_or_none()

async def create_permission(db: AsyncSession, data: PermissionCreate):
    permission = Permission(**data.model_dump())
    db.add(permission)
    await db.commit()
    await db.refresh(permission)
    return permission

async def update_permission(db: AsyncSession, permission_id: int, data: PermissionUpdate):
    permission = await get_permission_by_id(db, permission_id)
    if not permission:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(permission, k, v)
    await db.commit()
    await db.refresh(permission)
    return permission

async def delete_permission(db: AsyncSession, permission_id: int):
    permission = await get_permission_by_id(db, permission_id)
    if not permission:
        return None
    await db.delete(permission)
    await db.commit()
    return {"message": "Permission deleted"}
