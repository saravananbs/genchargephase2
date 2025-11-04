from enum import Enum
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

# --- AutoPay Enum ---
class AutoPayStatus(Enum):
    enabled = "enabled"
    disabled = "disabled"

class AutoPayTag(Enum):
    onetime = "onetime"
    regular = "regular"

# --- AutoPay ORM Model ---
class AutoPay(Base):
    __tablename__ = "AutoPay"

    autopay_id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("Users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    plan_id = Column(
        Integer,
        ForeignKey("Plans.plan_id", ondelete="CASCADE"),
        nullable=False
    )
    status = Column(String, nullable=False)  # Using String to store enum value
    phone_number = Column(String, nullable=False)
    tag = Column(String, nullable=False)      # Using String to store enum value
    next_due_date = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships (optional but useful)
    user = relationship("User", back_populates="autopays")
    plan = relationship("Plan", back_populates="autopays")