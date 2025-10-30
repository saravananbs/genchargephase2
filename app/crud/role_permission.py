from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.roles_permissions import RolePermission
from ..schemas.role_permission import RolePermissionCreate

async def get_role_permissions(db: AsyncSession):
    result = await db.execute(select(RolePermission))
    return result.scalars().all()

async def get_permissions_by_role(db: AsyncSession, role_id: int):
    result = await db.execute(select(RolePermission).where(RolePermission.role_id == role_id))
    return result.scalars().all()

async def assign_permission_to_role(db: AsyncSession, data: RolePermissionCreate):
    mapping = RolePermission(**data.model_dump())
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)
    return mapping

async def remove_permission_from_role(db: AsyncSession, role_id: int, permission_id: int):
    result = await db.execute(
        select(RolePermission).where(RolePermission.role_id == role_id, RolePermission.permission_id == permission_id)
    )
    mapping = result.scalar_one_or_none()
    if mapping:
        await db.delete(mapping)
        await db.commit()
    return {"message": "Permission removed from role"}
