from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..crud import users as crud_pref
from ..schemas.users import UserPreferenceUpdate

async def update_preferences_service(db: AsyncSession, user_id: int, data: UserPreferenceUpdate):
    """
    Update a user's preferences using the CRUD layer.

    Args:
        db (AsyncSession): Async SQLAlchemy session.
        user_id (int): ID of the user whose preferences are being updated.
        data (UserPreferenceUpdate): Pydantic object containing preference fields.

    Returns:
        The updated preference object returned by the CRUD layer.

    Raises:
        HTTPException: 404 if the user's preferences are not found.
    """
    updated_pref = await crud_pref.update_user_preference(db, user_id, data)
    if not updated_pref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User preferences not found")
    return updated_pref
