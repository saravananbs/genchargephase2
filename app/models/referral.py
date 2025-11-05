# app/models/referral.py  
from enum import Enum
from sqlalchemy import (
    Column, Integer, Numeric, String, TIMESTAMP, ForeignKey, func
)
from sqlalchemy.orm import relationship
from ..core.database import Base

class ReferralRewardStatus(str, Enum):
    pending = "pending"
    earned  = "earned"

class ReferralReward(Base):
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