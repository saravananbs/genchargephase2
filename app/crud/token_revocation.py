# crud/token_revocation.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.token_revocation import TokenRevocation
import datetime

async def revoke_token(
    db: AsyncSession,
    jti: str,
    refresh_token: str,
    user_id: int,
    reason: str,
    expires_at: datetime.datetime
):
    revocation = TokenRevocation(
        refresh_token_jti=jti,
        refresh_token=refresh_token,
        user_id=user_id,
        revoked_at=datetime.datetime.utcnow(),
        reason=reason,
        expires_at=expires_at
    )

    db.add(revocation)
    await db.commit()
    await db.refresh(revocation)
    return revocation

async def is_token_revoked(db: AsyncSession, jti: str) -> bool:
    result = await db.execute(
        select(TokenRevocation).where(TokenRevocation.refresh_token_jti == jti)
    )
    token = result.scalars().first()
    return token is not None
