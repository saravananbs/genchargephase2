# crud/roles.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import delete
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from ..models.roles import Role
from ..models.permissions import Permission
from ..models.roles_permissions import RolePermission
from typing import Optional, List

async def get_all_roles(db: AsyncSession):
    result = await db.execute(
        select(Role)
        .options(
            selectinload(Role.role_permissions)
            .selectinload(RolePermission.permission)
        )
    )
    roles = result.scalars().unique().all()
    return roles

async def get_role_by_id(db: AsyncSession, role_id: int):
    result = await db.execute(
        select(Role)
        .options(
            selectinload(Role.role_permissions)
            .selectinload(RolePermission.permission)
        ).where(Role.role_id == role_id)
    )
    role = result.scalars().unique().first()
    return role

async def create_role(db: AsyncSession, role_name: str, permission_ids: list[int]):
    try:
        new_role = Role(role_name=role_name)
        db.add(new_role)
        await db.commit()
        await db.refresh(new_role)

        for pid in permission_ids:
            db.add(RolePermission(role_id=new_role.role_id, permission_id=pid))
        await db.commit()
        result = await db.execute(
            select(Role)
            .where(Role.role_id == new_role.role_id)
            .options(selectinload(Role.role_permissions).selectinload(RolePermission.permission))
        )
        return result.scalar_one()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Role name already exists or Permission id is invalid")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def update_role(
    db: AsyncSession,
    role_id: int,
    role_name: Optional[str] = None,
    permission_ids: Optional[List[int]] = None
) -> Role:
    result = await db.execute(
        select(Role)
        .where(Role.role_id == role_id)
        .options(
            selectinload(Role.role_permissions).selectinload(RolePermission.permission)
        )
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    if role_name is not None:
        role.role_name = role_name

    if permission_ids is not None:
        await db.execute(
            delete(RolePermission).where(RolePermission.role_id == role_id)
        )

        if permission_ids:
            perm_result = await db.execute(
                select(Permission.permission_id).where(
                    Permission.permission_id.in_(permission_ids)
                )
            )
            existing_ids = set(perm_result.scalars()) 

            missing = set(permission_ids) - existing_ids
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Permissions not found: {sorted(missing)}"
                )

            new_links = [
                RolePermission(role_id=role_id, permission_id=pid)
                for pid in permission_ids
            ]
            db.add_all(new_links)

    await db.commit()
    await db.refresh(role)

    result = await db.execute(
        select(Role)
        .where(Role.role_id == role_id)
        .options(
            selectinload(Role.role_permissions).selectinload(RolePermission.permission)
        )
    )
    role = result.scalar_one()  

    return role

async def delete_role(db: AsyncSession, role_id: int):
    role = await get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    await db.delete(role)
    await db.commit()
    return {"message": "Role deleted successfully"}

async def get_all_permissions(db: AsyncSession):
    result = await db.execute(select(Permission))
    return result.scalars().all()
