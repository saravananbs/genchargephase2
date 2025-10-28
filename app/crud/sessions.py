# crud/sessions.py
from sqlalchemy.orm import Session
from ..models.sessions import Session as DBSession
from uuid import uuid4, UUID
import datetime

def create_session(db: Session, user_id: int, refresh_token: str, jti: str, expires_at: datetime.datetime):
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
    db.commit()
    db.refresh(db_session)
    return db_session

def get_session_by_jti(db: Session, jti: str):
    return db.query(DBSession).filter(DBSession.jti == jti).first()

def revoke_session(db: Session, session_id: UUID):
    session = db.query(DBSession).filter(DBSession.session_id == session_id).first()
    if session:
        session.is_active = False
        session.revoked_at = datetime.datetime.now()
        db.commit()
        db.refresh(session)
    return session