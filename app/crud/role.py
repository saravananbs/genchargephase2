from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.roles import Role
from app.schemas.role import RoleCreate, RoleUpdate

async def get_roles(db: AsyncSession):
    result = await db.execute(select(Role))
    return result.scalars().all()

async def get_role_by_id(db: AsyncSession, role_id: int):
    result = await db.execute(select(Role).where(Role.role_id == role_id))
    return result.scalar_one_or_none()

async def create_role(db: AsyncSession, data: RoleCreate):
    new_role = Role(**data.model_dump())
    db.add(new_role)
    await db.commit()
    await db.refresh(new_role)
    return new_role

async def update_role(db: AsyncSession, role_id: int, data: RoleUpdate):
    role = await get_role_by_id(db, role_id)
    if not role:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(role, key, value)
    await db.commit()
    await db.refresh(role)
    return role

async def delete_role(db: AsyncSession, role_id: int):
    role = await get_role_by_id(db, role_id)
    if not role:
        return None
    await db.delete(role)
    await db.commit()
    return {"message": "Role deleted"}
