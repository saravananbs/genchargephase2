# crud/permissions.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.roles import Role
from ..models.permissions import Permission
from ..schemas.permissions import PermissionCreate, PermissionUpdate
from ..models.roles_permissions import RolePermission

async def get_permissions_by_role(db: AsyncSession, role_name: str):
    """
    Fetch all permissions assigned to a given role.

    Args:
        db (AsyncSession): Async database session.
        role_name (str): Name of the role to look up permissions for.

    Returns:
        List[Permission]: List of Permission objects assigned to the role.
    """
    stmt = (
        select(Permission)
        .join(RolePermission, Permission.permission_id == RolePermission.permission_id)
        .join(Role, Role.role_id == RolePermission.role_id)
        .where(Role.role_name == role_name)
    )

    result = await db.execute(stmt)
    return result.scalars().all()

async def get_permissions(db: AsyncSession):
    """
    Retrieve all permissions in the system.

    Args:
        db (AsyncSession): Async database session.

    Returns:
        List[Permission]: List of all Permission instances.
    """
    result = await db.execute(select(Permission))
    return result.scalars().all()

async def get_permission_by_id(db: AsyncSession, permission_id: int):
    """
    Retrieve a permission by its ID.

    Args:
        db (AsyncSession): Async database session.
        permission_id (int): Primary key of the permission.

    Returns:
        Optional[Permission]: Permission instance if found, otherwise None.
    """
    result = await db.execute(select(Permission).where(Permission.permission_id == permission_id))
    return result.scalar_one_or_none()

async def create_permission(db: AsyncSession, data: PermissionCreate):
    """
    Create a new permission record.

    Args:
        db (AsyncSession): Async database session.
        data (PermissionCreate): Pydantic schema with permission creation data.

    Returns:
        Permission: The newly created Permission instance.
    """
    permission = Permission(**data.model_dump())
    db.add(permission)
    await db.commit()
    await db.refresh(permission)
    return permission

async def update_permission(db: AsyncSession, permission_id: int, data: PermissionUpdate):
    """
    Update an existing permission.

    Args:
        db (AsyncSession): Async database session.
        permission_id (int): ID of the permission to update.
        data (PermissionUpdate): Updated permission data.

    Returns:
        Optional[Permission]: Updated Permission instance, or None if not found.
    """
    permission = await get_permission_by_id(db, permission_id)
    if not permission:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(permission, k, v)
    await db.commit()
    await db.refresh(permission)
    return permission

async def delete_permission(db: AsyncSession, permission_id: int):
    """
    Delete a permission from the system.

    Args:
        db (AsyncSession): Async database session.
        permission_id (int): ID of the permission to delete.

    Returns:
        Optional[dict]: Status message if successful, or None if permission not found.
    """
    permission = await get_permission_by_id(db, permission_id)
    if not permission:
        return None
    await db.delete(permission)
    await db.commit()
    return {"message": "Permission deleted"}
