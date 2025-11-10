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
    """
    Revoke a JWT refresh token and record the revocation details.

    Args:
        db (AsyncSession): Async database session.
        jti (str): JWT ID (jti) claim to revoke.
        refresh_token (str): The refresh token string to revoke.
        user_id (int): ID of the user whose token is being revoked.
        reason (str): Reason for revoking the token.
        expires_at (datetime.datetime): Expiration time of the token.

    Returns:
        TokenRevocation: The newly created token revocation record.
    """
    revocation = TokenRevocation(
        refresh_token_jti=jti,
        refresh_token=refresh_token,
        user_id=user_id,
        revoked_at=datetime.datetime.now(),
        reason=reason,
        expires_at=expires_at
    )

    db.add(revocation)
    await db.commit()
    await db.refresh(revocation)
    return revocation

async def is_token_revoked(db: AsyncSession, jti: str) -> bool:
    """
    Check if a JWT refresh token (identified by JTI) has been revoked.

    Args:
        db (AsyncSession): Async database session.
        jti (str): JWT ID to check for revocation status.

    Returns:
        bool: True if token is revoked, False otherwise.
    """
    result = await db.execute(
        select(TokenRevocation).where(TokenRevocation.refresh_token_jti == jti)
    )
    token = result.scalars().first()
    return token is not None
