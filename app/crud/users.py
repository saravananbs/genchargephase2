# crud/users.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ..models.users import User
from ..schemas.users import UserCreate
from datetime import datetime


async def create_user(db: AsyncSession, user: UserCreate):
    db_user = User(
        name=user.name,
        email=user.email,
        phone_number=user.phone_number,
        referral_code=user.referral_code,
        referred_by=user.referred_by,
        user_type=user.user_type,
        status=user.status,
        wallet_balance=user.wallet_balance,
        created_at=user.created_at or datetime.utcnow(),
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_phone(db: AsyncSession, phone: str):
    result = await db.execute(select(User).where(User.phone_number == phone))
    return result.scalar_one_or_none()


async def update_user_status(db: AsyncSession, user_id: int, status: str):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.status = status
        await db.commit()
        await db.refresh(user)
    return user
