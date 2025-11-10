# models/sessions.py
from sqlalchemy import Column, UUID, Integer, Text, TIMESTAMP, Boolean, ForeignKey
from ..core.database import Base
import uuid

class Session(Base):
    """
    User session model tracking active authentication sessions and tokens.

    Attributes:
        session_id (UUID): Primary key unique session identifier.
        user_id (int): ID of the authenticated user.
        refresh_token (str): Unique refresh token for obtaining new access tokens.
        jti (UUID): JWT Token ID (unique identifier for JWT claims).
        refresh_token_expires_at (TIMESTAMP): Expiration time of refresh token.
        login_time (TIMESTAMP): Timestamp when user logged in.
        last_active (TIMESTAMP): Timestamp of last activity in this session.
        is_active (bool): Flag indicating if session is currently active.
        revoked_at (TIMESTAMP): Timestamp when session was revoked (nullable).
    """
    __tablename__ = "Sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer)
    refresh_token = Column(Text, unique=True, nullable=False)
    jti = Column(UUID(as_uuid=True), unique=True, nullable=False)
    refresh_token_expires_at = Column(TIMESTAMP, nullable=False)
    login_time = Column(TIMESTAMP)
    last_active = Column(TIMESTAMP)
    is_active = Column(Boolean, default=True)
    revoked_at = Column(TIMESTAMP)