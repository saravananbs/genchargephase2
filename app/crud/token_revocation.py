# crud/token_revocation.py
from sqlalchemy.orm import Session
from ..models.token_revocation import TokenRevocation
import datetime

def revoke_token(db: Session, jti: str, refresh_token: str, user_id: int, reason: str, expires_at: datetime.datetime):
    revocation = TokenRevocation(
        refresh_token_jti=jti,
        refresh_token=refresh_token,
        user_id=user_id,
        revoked_at=datetime.datetime.now(),
        reason=reason,
        expires_at=expires_at
    )
    db.add(revocation)
    db.commit()
    db.refresh(revocation)
    return revocation

def is_token_revoked(db: Session, jti: str):
    return db.query(TokenRevocation).filter(TokenRevocation.refresh_token_jti == jti).first() is not None