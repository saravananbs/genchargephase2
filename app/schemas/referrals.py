# app/schemas/referral.py
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field

class ReferralRewardStatus(str, Enum):
    """Enumeration for referral reward status values.
    
    Attributes:
        pending (str): Reward is pending and not yet earned.
        earned (str): Reward has been earned by the referrer.
    """
    pending = "pending"
    earned = "earned"

class ReferralRewardOut(BaseModel):
    """Referral reward information for API responses.
    
    Attributes:
        reward_id (int): Unique identifier for the reward.
        referrer_id (int): ID of the user who made the referral.
        referred_id (int): ID of the user who was referred.
        reward_amount (Decimal): Monetary reward amount.
        status (ReferralRewardStatus): Current reward status (pending/earned).
        created_at (datetime): Timestamp when reward was created.
        claimed_at (Optional[datetime]): Timestamp when reward was claimed/earned. None if pending.
    """
    reward_id: int
    referrer_id: int
    referred_id: int
    referrer_user_name: Optional[str] = None
    referrer_user_phone_number: Optional[str] = None
    referred_user_name: Optional[str] = None
    referred_user_phone_number: Optional[str] = None
    reward_amount: Decimal
    status: ReferralRewardStatus
    created_at: datetime
    claimed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PaginatedReferralReward(BaseModel):
    """Paginated response for referral reward list queries.
    
    Attributes:
        items (list[ReferralRewardOut]): List of referral reward objects.
        total (int): Total number of rewards matching query.
        page (int): Current page number.
        size (int): Items per page.
        pages (int): Total number of pages.
    """
    items: list[ReferralRewardOut]
    total: int
    page: int
    size: int
    pages: int