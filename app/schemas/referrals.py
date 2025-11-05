# app/schemas/referral.py
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field

class ReferralRewardStatus(str, Enum):
    pending = "pending"
    earned = "earned"

class ReferralRewardOut(BaseModel):
    reward_id: int
    referrer_id: int
    referred_id: int
    reward_amount: Decimal
    status: ReferralRewardStatus
    created_at: datetime
    claimed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PaginatedReferralReward(BaseModel):
    items: list[ReferralRewardOut]
    total: int
    page: int
    size: int
    pages: int