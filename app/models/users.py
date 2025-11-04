# models/users.py
from sqlalchemy import Column, Integer, String, Enum, Numeric, TIMESTAMP
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum

class UserType(enum.Enum):
    prepaid = "prepaid"
    postpaid = "postpaid"

class UserStatus(enum.Enum):
    active = "active"
    blocked = "blocked"
    deactive = "deactive"

class User(Base):
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
    