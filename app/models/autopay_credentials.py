from enum import Enum

from sqlalchemy import Column, Integer, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import relationship

from ..core.database import Base


class AutoPayCredentialType(str, Enum):
    """Supported payment instruments for autopay credentials."""
    upi = "upi"
    bank = "bank"
    card = "card"


class AutoPayCredential(Base):
    """Stores the user's autopay payment credentials in a structured format."""

    __tablename__ = "autopay_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("Users.user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    payment_type = Column(
        SAEnum(AutoPayCredentialType, name="autopay_payment_type_enum"),
        nullable=False,
    )
    credentials = Column(JSON, nullable=False)

    user = relationship("User", back_populates="autopay_credential")
