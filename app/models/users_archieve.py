# models/users_archieve.py
from sqlalchemy import Column, Integer, String, Enum, Numeric, TIMESTAMP, ForeignKey
from ..core.database import Base
import enum

class UserType(enum.Enum):
    """
    Enumeration of user type values for archived users.

    Values:
        prepaid: Archived prepaid service user.
        postpaid: Archived postpaid service user.
    """
    prepaid = "prepaid"
    postpaid = "postpaid"

class UserStatus(enum.Enum):
    """
    Enumeration of user status values for archived users.

    Values:
        active: User was active when archived.
        blocked: User was blocked when archived.
        deactive: User was deactivated when archived.
    """
    active = "active"
    blocked = "blocked"
    deactive = "deactive"

class UserArchieve(Base):
    """
    Archived user model storing historical records of deleted users.

    This table maintains a permanent record of users who have deleted their accounts.

    Attributes:
        user_id (int): Original user ID (primary key in this archive).
        name (str): User's full name at time of deletion.
        email (str): User's email address at time of deletion.
        phone_number (str): User's phone number at time of deletion.
        referral_code (str): User's referral code at time of deletion.
        referee_code (str): Referral code of the referrer at time of deletion.
        user_type (UserType): Service type at time of deletion.
        status (UserStatus): Account status at time of deletion.
        wallet_balance (Numeric): Remaining wallet balance at deletion.
        created_at (TIMESTAMP): Original account creation timestamp.
        deleted_at (TIMESTAMP): Timestamp when account was deleted/archived.
    """
    __tablename__ = "UsersArchieve"

    user_id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    phone_number = Column(String)
    referral_code = Column(String, unique=True)
    referee_code = Column(String)
    user_type = Column(Enum(UserType))
    status = Column(Enum(UserStatus))
    wallet_balance = Column(Numeric(10, 2), default=0)
    created_at = Column(TIMESTAMP)
    deleted_at = Column(TIMESTAMP)
    