from ..core.database import Base
from sqlalchemy import Column, Integer, ForeignKey, String, TIMESTAMP, Enum
from sqlalchemy.orm import relationship
import enum

class CurrentPlanStatus(enum.Enum):
    active = "active"
    expired = "expired"
    queued = "queued"

class CurrentActivePlan(Base):
    __tablename__ = "CurrentActivePlans"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("Users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    plan_id = Column(
        Integer,
        ForeignKey("Plans.plan_id", ondelete="CASCADE"),
        nullable=False
    )
    phone_number = Column(String, nullable=False)
    valid_from = Column(TIMESTAMP, nullable=False)
    valid_to = Column(TIMESTAMP, nullable=False)
    status = Column(Enum(CurrentPlanStatus), nullable=False)

    plan = relationship("Plan", back_populates="active_plans")
    user = relationship("User")
