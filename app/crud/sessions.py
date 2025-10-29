# crud/sessions.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.sessions import Session as DBSession
from uuid import uuid4, UUID
import datetime


async def create_session(
    db: AsyncSession,
    user_id: int,
    refresh_token: str,
    jti: str,
    expires_at: datetime.datetime
):
    db_session = DBSession(
        session_id=uuid4(),
        user_id=user_id,
        refresh_token=refresh_token,
        jti=jti,
        refresh_token_expires_at=expires_at,
        login_time=datetime.datetime.now(),
        last_active=datetime.datetime.now(),
        is_active=True
    )

    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session


async def get_session_by_jti(db: AsyncSession, jti: str):
    result = await db.execute(select(DBSession).where(DBSession.jti == jti))
    return result.scalars().first()


async def revoke_session(db: AsyncSession, session_id: UUID):
    result = await db.execute(select(DBSession).where(DBSession.session_id == session_id))
    session = result.scalars().first()

    if session:
        session.is_active = False
        session.revoked_at = datetime.datetime.now()
        await db.commit()
        await db.refresh(session)

    return session
