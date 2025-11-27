from fastapi import HTTPException
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession

from ..crud.autopay_credentials import (
    get_autopay_credentials_by_user,
    upsert_autopay_credentials,
)
from ..schemas.autopay_credentials import (
    AutoPayCredentialOut,
    AutoPayCredentialUpsert,
)


async def fetch_user_autopay_credentials(
    db: AsyncSession, *, user_id: int
) -> AutoPayCredentialOut:
    """Load saved autopay credentials for the current user."""
    credentials = await get_autopay_credentials_by_user(db, user_id=user_id)
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Autopay credentials not found",
        )
    return AutoPayCredentialOut.model_validate(credentials)


async def replace_user_autopay_credentials(
    db: AsyncSession, *, user_id: int, obj_in: AutoPayCredentialUpsert
) -> AutoPayCredentialOut:
    """Replace the user's autopay credentials atomically."""
    updated = await upsert_autopay_credentials(db, user_id=user_id, obj_in=obj_in)
    return AutoPayCredentialOut.model_validate(updated)
