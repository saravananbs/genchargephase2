from enum import Enum
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

# --- AutoPay Enum ---
class AutoPayStatus(Enum):
    """
    Enumeration of autopay status values.

    Values:
        enabled: Autopay is active and will process recurring payments.
        disabled: Autopay is inactive and will not process payments.
    """
    enabled = "enabled"
    disabled = "disabled"

class AutoPayTag(Enum):
    """
    Enumeration of autopay tag/type values.

    Values:
        onetime: Autopay configured for a single one-time payment.
        regular: Autopay configured for recurring regular payments.
    """
    onetime = "onetime"
    regular = "regular"

# --- AutoPay ORM Model ---
class AutoPay(Base):
    """
    Autopay subscription model for recurring or one-time automated payments.

    Attributes:
        autopay_id (int): Primary key identifier for the autopay record.
        user_id (int): Foreign key to the User making the autopay.
        plan_id (int): Foreign key to the Plan associated with autopay.
        status (str): Autopay status ('enabled' or 'disabled').
        phone_number (str): Target phone number for the autopay transaction.
        tag (str): Autopay tag type ('onetime' or 'regular').
        next_due_date (TIMESTAMP): Date/time when autopay is next due to process.
        created_at (TIMESTAMP): Timestamp of autopay creation.
        user (User): Relationship to the associated User object.
        plan (Plan): Relationship to the associated Plan object.
    """
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