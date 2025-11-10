from ..core.database import Base
from sqlalchemy import Column, Integer, Boolean, Enum, ForeignKey, Text, JSON, TIMESTAMP, func, String
from sqlalchemy.orm import relationship
import enum

class PlanType(enum.Enum):
    """
    Enumeration of plan type values.

    Values:
        prepaid: Prepaid plan requiring upfront payment.
        postpaid: Postpaid plan with billing after service usage.
    """
    prepaid = "prepaid"
    postpaid = "postpaid"


class PlanStatus(enum.Enum):
    """
    Enumeration of plan status values.

    Values:
        active: Plan is currently active and available for purchase.
        inactive: Plan is inactive and not available.
    """
    active = "active"
    inactive = "inactive"

class Plan(Base):
    """
    Recharge/subscription plan model representing service offerings.

    Attributes:
        plan_id (int): Primary key identifier for the plan.
        plan_name (str): Name/title of the plan.
        validity (int): Validity period of the plan in days.
        most_popular (bool): Flag marking if this is a popular/featured plan.
        plan_type (PlanType): Type of plan (prepaid or postpaid).
        group_id (int): Foreign key to PlanGroup.
        description (str): Detailed description of the plan.
        criteria (JSON): JSON criteria/conditions for plan eligibility.
        created_at (TIMESTAMP): Timestamp when plan was created.
        created_by (int): Admin user ID who created the plan.
        price (int): Price of the plan in minor currency units.
        status (PlanStatus): Plan status (active or inactive).
        group (PlanGroup): Relationship to the PlanGroup object.
        active_plans (List[CurrentActivePlan]): Relationship to active plan instances.
        autopays (List[AutoPay]): Relationship to AutoPay records for this plan.
    """
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

setattr(Plan, "autopays", relationship("AutoPay", back_populates="plan", passive_deletes=True))
