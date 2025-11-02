from sqlalchemy import Column, UUID, Integer, TIMESTAMP, String, ForeignKey
from ..core.database import Base

class TokenRevocation(Base):
    __tablename__ = "TokenRevocation"

    refresh_token_jti = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False)
    refresh_token = Column(String)
    user_id = Column(Integer)
    revoked_at = Column(TIMESTAMP, default="now()")
    reason = Column(String(100))
    expires_at = Column(TIMESTAMP)
