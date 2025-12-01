# crud/users.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_, asc, desc
from ..models.users import User, UserStatus, UserType
from ..models.users_archieve import UserArchieve
from ..models.referral import ReferralReward, ReferralRewardStatus
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
    """
    Create a new user record in the database.

    This generates a unique referral code, constructs a User model from the
    provided schema, commits it to the database and returns the persisted
    User instance.

    Args:
        db (AsyncSession): Async database session.
        user (UserCreatenew): Pydantic schema containing user creation data.

    Returns:
        User: The newly created and refreshed User ORM instance.
    """
    referal_code = await generate_unique_referral_code(db)
    db_user = User(
        name=user.name,
        email=user.email,
        phone_number=user.phone_number,
        referral_code=referal_code,
        referee_code =user.referee_code,
        status=user.status,
        wallet_balance=user.wallet_balance,
        created_at=user.created_at or datetime.now(),
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_user_by_email(db: AsyncSession, email: str):
    """
    Retrieve a user by their email address.

    Args:
        db (AsyncSession): Async database session.
        email (str): Email address to search for.

    Returns:
        Optional[User]: User instance if found, otherwise None.
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_phone(db: AsyncSession, phone: str):
    """
    Retrieve a user by phone number.

    Args:
        db (AsyncSession): Async database session.
        phone (str): Phone number string.

    Returns:
        Optional[User]: User instance if found, otherwise None.
    """
    result = await db.execute(select(User).where(User.phone_number == phone))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int):
    """
    Retrieve a user by their numeric ID.

    Args:
        db (AsyncSession): Async database session.
        user_id (int): Primary key of the user.

    Returns:
        Optional[User]: User instance if found, otherwise None.
    """
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()


async def update_user_status(db: AsyncSession, user_id: int, status: str):
    """
    Update the status field of a user.

    Args:
        db (AsyncSession): Async database session.
        user_id (int): ID of the user to update.
        status (str): New status value.

    Returns:
        Optional[User]: Updated User instance, or None if user not found.
    """
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.status = status
        user.updated_at = datetime.now()
        await db.commit()
        await db.refresh(user)
    return user


async def get_users(db: AsyncSession, filters: UserListFilters) -> Sequence[User]:
    """
    Retrieve a paginated list of users using the provided filters.

    Supports filtering by name, status, user_type and sorting.

    Args:
        db (AsyncSession): Async database session.
        filters (UserListFilters): Filter and pagination options.

    Returns:
        Sequence[User]: List of User ORM instances matching the filters.
    """
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
    if filters.skip > 0 or filters.limit >0:
        stmt = stmt.offset(filters.skip).limit(filters.limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def delete_user(db: AsyncSession, user_id: int) -> Optional[UserArchieve]:
    """
    Archive and delete a user record.

    Creates a UserArchieve record from the existing User, deletes the
    original User row and returns the archive entry. If the user does not
    exist, returns None.

    Args:
        db (AsyncSession): Async database session.
        user_id (int): ID of the user to delete.

    Returns:
        Optional[UserArchieve]: The archived user record, or None if not found.
    """
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
    """
    List archived users with the same filtering and pagination semantics as `get_users`.

    Args:
        db (AsyncSession): Async database session.
        filters (UserListFilters): Filter and pagination options.

    Returns:
        Sequence[UserArchieve]: List of archived user records.
    """
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
    """
    Block a user by setting their status to `blocked`.

    Validates current state and raises an HTTPException for invalid transitions.

    Args:
        db (AsyncSession): Async database session.
        user_id (int): ID of the user to block.

    Returns:
        Optional[User]: Updated User instance, or None if user not found.

    Raises:
        HTTPException: If the user is already blocked or not active.
    """
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
    """
    Unblock a user by setting their status to `active`.

    Args:
        db (AsyncSession): Async database session.
        user_id (int): ID of the user to unblock.

    Returns:
        Optional[User]: Updated User instance, or None if user not found.

    Raises:
        HTTPException: If the user is already active or not active (invalid transition).
    """
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
    """
    Update a user's email address.

    Args:
        db (AsyncSession): Async database session.
        user_id (int): ID of the user to update.
        new_email (str): New email address.

    Returns:
        Optional[User]: Updated User instance, or None if user not found.
    """
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
    """
    Change the user's type (e.g., prepaid/postpaid).

    Args:
        db (AsyncSession): Async database session.
        user_id (int): ID of the user to update.
        user_type (UserType): New user type enum value.

    Returns:
        Optional[User]: Updated User instance, or None if user not found.
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    user.user_type = user_type
    user.updated_at = datetime.now()
    await db.commit()
    await db.refresh(user)
    return user


async def deactivate_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Deactivate a user (set status to `deactive`).

    Args:
        db (AsyncSession): Async database session.
        user_id (int): ID of the user to deactivate.

    Returns:
        Optional[User]: Updated User instance, or None if user not found.

    Raises:
        HTTPException: If the user is blocked or already deactivated.
    """
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
    """
    Reactivate a user (set status to `active`).

    Args:
        db (AsyncSession): Async database session.
        user_id (int): ID of the user to reactivate.

    Returns:
        Optional[User]: Updated User instance, or None if user not found.

    Raises:
        HTTPException: If the user is already active or is blocked.
    """
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
    """
    Convenience wrapper to archive and delete a user account.

    Args:
        db (AsyncSession): Async database session.
        user_id (int): ID of the user to delete.

    Returns:
        Optional[UserArchieve]: The archived user record, or None if not found.
    """
    return await delete_user(db, user_id)


async def register_user(
    db: AsyncSession,
    current_user: User,
    name: str,
    email: str,
    user_type: str,
    referee_code: Optional[str] = None,
) -> User:
    """
    Complete the registration process for a partially created user.

    This updates the provided `current_user` with name/email and optionally
    creates a `ReferralReward` if a valid referee code is supplied.

    Args:
        db (AsyncSession): Async database session.
        current_user (User): Existing user instance to update.
        name (str): Name to set.
        email (str): Email to set.
        referee_code (Optional[str]): Optional referral code of the referrer.

    Returns:
        User: The updated user instance.

    Raises:
        HTTPException: For invalid referee codes or if the user is already registered.
    """
    # --- Step 1: Check if user is already registered ---
    stmt = select(User).where(
        User.user_id == current_user.user_id,
        or_(
            User.name.is_not(None),
            User.email.is_not(None),
            User.referee_code.is_not(None),
        ),
    )
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already registered",
        )

    # --- Step 2: Validate referee_code (if provided) ---
    referrer = None
    if referee_code:
        stmt = select(User).where(User.referral_code == referee_code)
        result = await db.execute(stmt)
        referrer = result.scalars().first()
        if not referrer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid referee code",
            )
        if referrer.user_id == current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot refer yourself",
            )

    # --- Step 3: Update user ---
    update_stmt = (
        update(User)
        .where(User.user_id == current_user.user_id)
        .values(
            name=name,
            email=email,
            referee_code=referee_code,
            user_type=user_type,
            updated_at=datetime.now(),
        )
        .execution_options(synchronize_session="fetch")
    )
    await db.execute(update_stmt)

    # --- Step 4: Create ReferralReward if referee exists ---
    if referrer:
        reward = ReferralReward(
            referrer_id=referrer.user_id,
            referred_id=current_user.user_id,
            reward_amount=50.00,  # configure via settings or plan
            status=ReferralRewardStatus.pending.value,
            created_at=datetime.now(),
        )
        db.add(reward)

    await db.commit()
    await db.refresh(current_user)
    return current_user


async def get_user_preference(db: AsyncSession, user_id: int):
    """
    Fetch the UserPreference record for a given user.

    Args:
        db (AsyncSession): Async database session.
        user_id (int): ID of the user whose preferences to fetch.

    Returns:
        Optional[UserPreference]: The preference record, or None if not set.
    """
    result = await db.execute(select(UserPreference).where(UserPreference.user_id == user_id))
    return result.scalars().first()


async def create_user_preference(db: AsyncSession, user_id: int, data: UserPreferenceUpdate):
    """
    Create a UserPreference record for the given user.

    Args:
        db (AsyncSession): Async database session.
        user_id (int): User ID to associate the preference with.
        data (UserPreferenceUpdate): Preference data schema.

    Returns:
        UserPreference: Persisted preference ORM instance.
    """
    preference = UserPreference(user_id=user_id, **data)
    db.add(preference)
    await db.commit()
    await db.refresh(preference)
    return preference


async def update_user_preference(db: AsyncSession, user_id: int, data: UserPreferenceUpdate):
    """
    Update (or create) a user's preferences.

    If preferences do not exist for the user, a new record will be created.

    Args:
        db (AsyncSession): Async database session.
        user_id (int): User to update preferences for.
        data (UserPreferenceUpdate): Preference values to set.

    Returns:
        UserPreference: The upserted preference record.
    """
    preference = await get_user_preference(db, user_id)
    if not preference:
        return await create_user_preference(db, user_id, data)

    for field, value in data.model_dump().items():
        setattr(preference, field, value)

    await db.commit()
    await db.refresh(preference)
    return preference
