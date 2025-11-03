# crud/users.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_, asc, desc
from ..models.users import User, UserStatus, UserType
from ..models.users_archieve import UserArchieve
from ..models.user_preference import UserPreference
from ..schemas.users import UserCreatenew, UserListFilters, UserPreferenceUpdate
from datetime import datetime
from typing import Optional, Sequence
from fastapi import HTTPException, status
import string
import random


async def generate_unique_referral_code(db: AsyncSession, length: int = 8) -> str:
    """Generate a unique alphanumeric referral code."""
    characters = string.ascii_uppercase + string.digits

    while True:
        code = ''.join(random.choices(characters, k=length))
        result = await db.execute(select(User).where(User.referral_code == code))
        existing_user = result.scalars().first()
        if not existing_user:
            return code


async def create_user(db: AsyncSession, user: UserCreatenew):
    referal_code = await generate_unique_referral_code(db)
    db_user = User(
        name=user.name,
        email=user.email,
        phone_number=user.phone_number,
        referral_code=referal_code,
        referee_code =user.referee_code,
        user_type=user.user_type,
        status=user.status,
        wallet_balance=user.wallet_balance,
        created_at=user.created_at or datetime.now(),
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


async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()


async def update_user_status(db: AsyncSession, user_id: int, status: str):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.status = status
        user.updated_at = datetime.now()
        await db.commit()
        await db.refresh(user)
    return user


async def get_users(db: AsyncSession, filters: UserListFilters) -> Sequence[User]:
    stmt = select(User)
    if filters.name:
        stmt = stmt.where(User.name.ilike(f"%{filters.name}%"))
    if filters.status:
        stmt = stmt.where(User.status == filters.status)
    if filters.user_type:
        stmt = stmt.where(User.user_type == filters.user_type)
    if filters.sort_by:
        column = getattr(User, filters.sort_by, None)
        if column is not None:
            if filters.sort_order == "desc":
                stmt = stmt.order_by(desc(column))
            else:
                stmt = stmt.order_by(asc(column))
    stmt = stmt.offset(filters.skip).limit(filters.limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def delete_user(db: AsyncSession, user_id: int) -> Optional[UserArchieve]:
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user: Optional[User] = user_result.scalar_one_or_none()
    if not user:
        return None
    
    user.user_type = "prepaid" if user.user_type == "UserType.prepaid" else "postpaid"
    user.status = "active" if user.status == "UserStatus.active" else "blocked"

    archived = UserArchieve(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        phone_number=user.phone_number,
        referral_code=user.referral_code,
        referee_code =user.referee_code,
        user_type=user.user_type,
        status=user.status,
        wallet_balance=user.wallet_balance,
        created_at=user.created_at,
        deleted_at=datetime.now(),
    )
    db.add(archived)

    await db.delete(user)

    await db.commit()
    return archived


async def get_archived_users(
    db: AsyncSession, filters: UserListFilters
) -> Sequence[UserArchieve]:
    stmt = select(UserArchieve)

    if filters.name:
        stmt = stmt.where(UserArchieve.name.ilike(f"%{filters.name}%"))
    if filters.status:
        stmt = stmt.where(UserArchieve.status == filters.status)
    if filters.user_type:
        stmt = stmt.where(UserArchieve.user_type == filters.user_type)
    if filters.sort_by:
        column = getattr(UserArchieve, filters.sort_by, None)
        if column is not None:
            if filters.sort_order == "desc":
                stmt = stmt.order_by(desc(column))
            else:
                stmt = stmt.order_by(asc(column))
    stmt = stmt.offset(filters.skip).limit(filters.limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def block_user(db: AsyncSession, user_id: int) -> Optional[User]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    if user.status == UserStatus.blocked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already blocked"
        )
    if user.status == UserStatus.deactive:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is not active, Cannot block a non-active user"
        )
    user.status = UserStatus.blocked
    user.updated_at = datetime.now()
    await db.commit()
    await db.refresh(user)
    return user


async def unblock_user(db: AsyncSession, user_id: int) -> Optional[User]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    if user.status == UserStatus.active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already active, Cannot unblock a active user"
        )
    if user.status == UserStatus.deactive:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is not active, Cannot unblock a active user"
        )

    user.status = UserStatus.active
    user.updated_at = datetime.now()
    await db.commit()
    await db.refresh(user)
    return user


async def update_email(
    db: AsyncSession, user_id: int, new_email: str
) -> Optional[User]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    user.email = new_email
    user.updated_at = datetime.now()
    await db.commit()
    await db.refresh(user)
    return user


async def switch_user_type(
    db: AsyncSession, user_id: int, user_type: UserType
) -> Optional[User]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    user.user_type = user_type
    user.updated_at = datetime.now()
    await db.commit()
    await db.refresh(user)
    return user


async def deactivate_user(db: AsyncSession, user_id: int) -> Optional[User]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    if user.status == UserStatus.blocked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already blocked, Cannot deactivate"
        )
    if user.status == UserStatus.deactive:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is not active, Cannot deactivate a non-active user"
        )
    user.status = UserStatus.deactive
    user.updated_at = datetime.now()
    await db.commit()
    await db.refresh(user)
    return user


async def reactivate_user(db: AsyncSession, user_id: int) -> Optional[User]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    if user.status == UserStatus.active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already active"
        )
    if user.status == UserStatus.blocked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is blocked, Cannot deactivate a blocked user"
        )

    user.status = UserStatus.active
    user.updated_at = datetime.now()
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user_account(db: AsyncSession, user_id: int) -> Optional[UserArchieve]:
    return await delete_user(db, user_id)


async def register_user(db: AsyncSession, current_user: User, name: str, email: str, referee_code: str = None):
    stmt = (
        select(User)
        .where(
            User.user_id == current_user.user_id,
            or_(
                User.name.isnot(None),
                User.email.isnot(None),
                User.referee_code.isnot(None)
            )
        )
    )
    result = await db.execute(stmt)    
    user = result.scalars().first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already registered"
        )
    stmt = (
        update(User)
        .where(User.user_id == current_user.user_id)
        .values(name=name, email=email, referee_code=referee_code, updated_at=datetime.now())
        .execution_options(synchronize_session="fetch")
    )
    await db.execute(stmt)
    await db.commit()

    updated_user = await db.get(User, current_user.user_id)
    return updated_user


async def get_user_preference(db: AsyncSession, user_id: int):
    result = await db.execute(select(UserPreference).where(UserPreference.user_id == user_id))
    return result.scalars().first()


async def create_user_preference(db: AsyncSession, user_id: int, data: UserPreferenceUpdate):
    preference = UserPreference(user_id=user_id, **data)
    db.add(preference)
    await db.commit()
    await db.refresh(preference)
    return preference


async def update_user_preference(db: AsyncSession, user_id: int, data: UserPreferenceUpdate):
    preference = await get_user_preference(db, user_id)
    if not preference:
        return await create_user_preference(db, user_id, data)

    for field, value in data.model_dump().items():
        setattr(preference, field, value)

    await db.commit()
    await db.refresh(preference)
    return preference
