# crud/admins.py
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.admins import Admin
from ..schemas.admin import AdminBase
import datetime

async def create_admin(db: AsyncSession, admin: AdminBase):
    db_admin = Admin(
        name=admin.name,
        email=admin.email,
        phone_number=admin.phone_number,
        status=admin.status,
        created_at=admin.created_at or datetime.datetime.now(),
        updated_at=admin.updated_at or datetime.datetime.now(),
        role_id=admin.role_id
    )

    db.add(db_admin)
    await db.commit()
    await db.refresh(db_admin)
    return db_admin


async def get_admin_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(Admin).where(Admin.email == email))
    return result.scalars().first()


async def get_admin_by_phone(db: AsyncSession, phone: str):
    result = await db.execute(select(Admin).where(Admin.phone_number == phone))
    return result.scalars().first()


async def update_admin_status(db: AsyncSession, admin_id: int, status: str):
    result = await db.execute(select(Admin).where(Admin.admin_id == admin_id))
    admin = result.scalars().first()
    if admin:
        admin.status = status
        admin.updated_at = datetime.datetime.now()
        await db.commit()
        await db.refresh(admin)
    return admin


async def get_admin_role_by_phone(db: AsyncSession, phone: str):
    result = await db.execute(
        select(Admin)
        .options(selectinload(Admin.role))  # ✅ eager load role
        .where(Admin.phone_number == phone)
    )
    admin = result.scalars().first()
    if admin and getattr(admin, "role", None):
        return admin.role
    return None
