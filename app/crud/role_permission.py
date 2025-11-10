from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.roles_permissions import RolePermission
from ..schemas.role_permission import RolePermissionCreate

async def get_role_permissions(db: AsyncSession):
    """
    Retrieve all role-permission mappings.

    Args:
        db (AsyncSession): Async database session.

    Returns:
        List[RolePermission]: All role-permission mapping records.
    """
    result = await db.execute(select(RolePermission))
    return result.scalars().all()

async def get_permissions_by_role(db: AsyncSession, role_id: int):
    """
    Retrieve all permissions assigned to a specific role.

    Args:
        db (AsyncSession): Async database session.
        role_id (int): ID of the role to retrieve permissions for.

    Returns:
        List[RolePermission]: Permissions assigned to the role.
    """
    result = await db.execute(select(RolePermission).where(RolePermission.role_id == role_id))
    return result.scalars().all()

async def assign_permission_to_role(db: AsyncSession, data: RolePermissionCreate):
    """
    Assign a permission to a role, creating a new role-permission mapping.

    Args:
        db (AsyncSession): Async database session.
        data (RolePermissionCreate): Role and permission IDs to map.

    Returns:
        RolePermission: The created role-permission mapping.
    """
    mapping = RolePermission(**data.model_dump())
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)
    return mapping

async def remove_permission_from_role(db: AsyncSession, role_id: int, permission_id: int):
    """
    Remove a permission from a role by deleting the role-permission mapping.

    Args:
        db (AsyncSession): Async database session.
        role_id (int): ID of the role.
        permission_id (int): ID of the permission to remove.

    Returns:
        Dict: Confirmation message.
    """
    result = await db.execute(
        select(RolePermission).where(RolePermission.role_id == role_id, RolePermission.permission_id == permission_id)
    )
    mapping = result.scalar_one_or_none()
    if mapping:
        await db.delete(mapping)
        await db.commit()
    return {"message": "Permission removed from role"}
