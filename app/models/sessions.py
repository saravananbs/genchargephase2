# models/sessions.py
from sqlalchemy import Column, UUID, Integer, Text, TIMESTAMP, Boolean, ForeignKey
from ..core.database import Base
import uuid

class Session(Base):
    __tablename__ = "Sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), nullable=False)
    refresh_token = Column(Text, unique=True, nullable=False)
    jti = Column(UUID(as_uuid=True), unique=True, nullable=False)
    refresh_token_expires_at = Column(TIMESTAMP, nullable=False)
    login_time = Column(TIMESTAMP)
    last_active = Column(TIMESTAMP)
    is_active = Column(Boolean, default=True)
    revoked_at = Column(TIMESTAMP)