from ..core.database import Base
from sqlalchemy import Column, Integer, Boolean, Enum, ForeignKey, Text, JSON, TIMESTAMP, func, String
from sqlalchemy.orm import relationship
import enum

class PlanType(enum.Enum):
    prepaid = "prepaid"
    postpaid = "postpaid"


class PlanStatus(enum.Enum):
    active = "active"
    inactive = "inactive"

class Plan(Base):
    __tablename__ = "Plans"

    plan_id = Column(Integer, primary_key=True)
    plan_name = Column(String, nullable=False)
    validity = Column(Integer)
    most_popular = Column(Boolean, default=False)
    plan_type = Column(Enum(PlanType), nullable=False)
    group_id = Column(
        Integer,
        ForeignKey("PlanGroups.group_id", ondelete="SET NULL"),
        nullable=True
    )
    description = Column(Text)
    criteria = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    created_by = Column(Integer, nullable=True)
    price = Column(Integer, nullable=False)
    status = Column(Enum(PlanStatus), nullable=False, default=PlanStatus.active)

    group = relationship("PlanGroup", back_populates="plans")
    active_plans = relationship("CurrentActivePlan", back_populates="plan", passive_deletes=True)
