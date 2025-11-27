from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.autopay_credentials import AutoPayCredential
from ..schemas.autopay_credentials import AutoPayCredentialUpsert


async def get_autopay_credentials_by_user(
    db: AsyncSession, *, user_id: int
) -> AutoPayCredential | None:
    """Return the stored autopay credentials for a specific user, if any."""
    stmt = select(AutoPayCredential).where(AutoPayCredential.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def upsert_autopay_credentials(
    db: AsyncSession, *, user_id: int, obj_in: AutoPayCredentialUpsert
) -> AutoPayCredential:
    """Create a new credentials record or replace the existing one for the user."""
    db_obj = await get_autopay_credentials_by_user(db, user_id=user_id)

    if db_obj is None:
        db_obj = AutoPayCredential(
            user_id=user_id,
            payment_type=obj_in.payment_type,
            credentials=obj_in.credentials,
        )
        db.add(db_obj)
    else:
        db_obj.payment_type = obj_in.payment_type
        db_obj.credentials = obj_in.credentials

    await db.commit()
    await db.refresh(db_obj)
    return db_obj
