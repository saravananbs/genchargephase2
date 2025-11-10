from sqlalchemy import Column, UUID, Integer, TIMESTAMP, String, ForeignKey
from ..core.database import Base

class TokenRevocation(Base):
    """
    Token revocation model for tracking invalidated JWT tokens and refresh tokens.

    Attributes:
        refresh_token_jti (UUID): Primary key representing the JWT Token ID (JTI claim).
        refresh_token (str): The actual refresh token string that was revoked.
        user_id (int): ID of the user whose token was revoked.
        revoked_at (TIMESTAMP): Timestamp when the token was revoked.
        reason (str): Reason for token revocation (e.g., 'logout', 'password_change').
        expires_at (TIMESTAMP): Expiration time of the revoked token.
    """
    __tablename__ = "TokenRevocation"

    refresh_token_jti = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False)
    refresh_token = Column(String)
    user_id = Column(Integer)
    revoked_at = Column(TIMESTAMP, default="now()")
    reason = Column(String(100))
    expires_at = Column(TIMESTAMP)
