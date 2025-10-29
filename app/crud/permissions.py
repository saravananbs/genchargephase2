# crud/permissions.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.roles import Role
from ..models.permissions import Permission
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
