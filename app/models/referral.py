# app/models/referral.py  
from enum import Enum
from sqlalchemy import (
    Column, Integer, Numeric, String, TIMESTAMP, ForeignKey, func
)
from sqlalchemy.orm import relationship
from ..core.database import Base

class ReferralRewardStatus(str, Enum):
    """
    Enumeration of referral reward status values.

    Values:
        pending: Reward has been created but not yet claimed/finalized.
        earned: Reward has been earned and is available to the referrer.
    """
    pending = "pending"
    earned  = "earned"

class ReferralReward(Base):
    """
    Referral reward model tracking incentives for user referrals.

    Attributes:
        reward_id (int): Primary key identifier for the reward.
        referrer_id (int): Foreign key to User who made the referral (referrer).
        referred_id (int): Foreign key to User who was referred (referred).
        reward_amount (Numeric): Amount of reward (in currency).
        status (str): Status of the reward (pending or earned).
        created_at (TIMESTAMP): Timestamp when referral was made.
        claimed_at (TIMESTAMP): Timestamp when reward was claimed (nullable).
        referrer (User): Relationship to the referring user.
        referred (User): Relationship to the referred user.
    """
    __tablename__ = "ReferralRewards"

    reward_id     = Column(Integer, primary_key=True)
    referrer_id   = Column(
        Integer,
        ForeignKey("Users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    referred_id   = Column(
        Integer,
        ForeignKey("Users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reward_amount = Column(Numeric(10, 2), nullable=False)
    status        = Column(String, nullable=False)         
    created_at    = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
    )
    claimed_at    = Column(
        TIMESTAMP,
        nullable=True,
    )

    referrer = relationship(
        "User",
        foreign_keys=[referrer_id],
        back_populates="referrals_given",
    )
    referred = relationship(
        "User",
        foreign_keys=[referred_id],
        back_populates="referrals_received",
    )