# models/users.py
from sqlalchemy import Column, Integer, String, Enum, Numeric, TIMESTAMP, ForeignKey
from ..core.database import Base
import enum

class UserType(enum.Enum):
    prepaid = "prepaid"
    postpaid = "postpaid"

class UserStatus(enum.Enum):
    active = "active"
    blocked = "blocked"

class User(Base):
    __tablename__ = "Users"

    user_id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    phone_number = Column(String, unique=True)
    referral_code = Column(String, unique=True)
    referred_by = Column(String, ForeignKey("Users.referral_code"))
    user_type = Column(Enum(UserType))
    status = Column(Enum(UserStatus))
    wallet_balance = Column(Numeric(10, 2), default=0)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    # role_id = Column(Integer)
    # hashed_password = Column(String)  # Added for potential password, but since OTP, maybe not used