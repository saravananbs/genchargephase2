# models/users.py
from sqlalchemy import Column, Integer, String, Enum, Numeric, TIMESTAMP
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum

class UserType(enum.Enum):
    """
    Enumeration of user type values.

    Values:
        prepaid: Prepaid service user.
        postpaid: Postpaid service user.
    """
    none = None
    prepaid = "prepaid"
    postpaid = "postpaid"

class UserStatus(enum.Enum):
    """
    Enumeration of user account status values.

    Values:
        active: User account is active.
        blocked: User account has been blocked/suspended.
        deactive: User account has been deactivated.
    """
    active = "active"
    blocked = "blocked"
    deactive = "deactive"

class User(Base):
    """
    User/customer account model representing end-users in the system.

    Attributes:
        user_id (int): Primary key identifier for the user.
        name (str): User's full name.
        email (str): User's email address.
        phone_number (str): Unique phone number for the user.
        referral_code (str): Unique referral code for this user to share.
        referee_code (str): Referral code of the user who referred this user.
        user_type (UserType): Type of user service (prepaid/postpaid).
        status (UserStatus): Current account status (active/blocked/deactive).
        wallet_balance (Numeric): Current wallet balance in currency.
        created_at (TIMESTAMP): Timestamp of account creation.
        updated_at (TIMESTAMP): Timestamp of last account update.
        autopays (List[AutoPay]): Relationship to AutoPay records for this user.
        referrals_given (List[ReferralReward]): Referrals made by this user.
        referrals_received (List[ReferralReward]): Referrals from others for this user.
    """
    __tablename__ = "Users"

    user_id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    phone_number = Column(String, unique=True)
    referral_code = Column(String, unique=True)
    referee_code = Column(String)
    user_type = Column(Enum(UserType))
    status = Column(Enum(UserStatus))
    wallet_balance = Column(Numeric(10, 2), default=0)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)

setattr(User, "autopays", relationship("AutoPay", back_populates="user", passive_deletes=True))
setattr(
    User,
    "referrals_given",
    relationship(
        "ReferralReward",
        foreign_keys="ReferralReward.referrer_id",
        back_populates="referrer",
        passive_deletes=True,
    ),
)

setattr(
    User,
    "referrals_received",
    relationship(
        "ReferralReward",
        foreign_keys="ReferralReward.referred_id",
        back_populates="referred",
        passive_deletes=True,
    ),
)
    