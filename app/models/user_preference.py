# models/user_preference.py
from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base

class UserPreference(Base):
    """
    User preference model storing notification and communication preferences.

    Attributes:
        id (int): Primary key identifier.
        user_id (int): Foreign key to User (one-to-one relationship).
        email_notification (bool): Enable/disable email notifications (default: True).
        sms_notification (bool): Enable/disable SMS notifications (default: True).
        marketing_communication (bool): Enable/disable marketing emails (default: False).
        recharge_remainders (bool): Enable/disable recharge reminders (default: True).
        promotional_offers (bool): Enable/disable promotional offer notifications (default: False).
        transactional_alerts (bool): Enable/disable transaction alerts (default: True).
        data_analytics (bool): Allow usage data analytics collection (default: True).
        third_party_integrations (bool): Allow third-party integrations (default: False).
        user (User): Relationship to the associated User object.
    """
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
