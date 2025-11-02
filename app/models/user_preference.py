# models/user_preference.py
from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base

class UserPreference(Base):
    __tablename__ = "UserPreferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), unique=True)

    email_notification = Column(Boolean, default=True)
    sms_notification = Column(Boolean, default=True)
    marketing_communication = Column(Boolean, default=False)
    recharge_remainders = Column(Boolean, default=True)
    promotional_offers = Column(Boolean, default=False)
    transactional_alerts = Column(Boolean, default=True)
    data_analytics = Column(Boolean, default=True)
    third_party_integrations = Column(Boolean, default=False)

    user = relationship("User", backref="preferences", uselist=False)
