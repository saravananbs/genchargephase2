from ..core.database import Base
from sqlalchemy import Column, Integer, ForeignKey, String, TIMESTAMP, Enum
from sqlalchemy.orm import relationship
import enum

class CurrentPlanStatus(enum.Enum):
    """
    Enumeration of current plan status values.

    Values:
        active: Plan is currently active and valid.
        expired: Plan validity period has passed.
        queued: Plan is queued and waiting to be activated.
    """
    active = "active"
    expired = "expired"
    queued = "queued"

class CurrentActivePlan(Base):
    """
    Model tracking currently active plans for users on specific phone numbers.

    Attributes:
        id (int): Primary key identifier.
        user_id (int): Foreign key to User owning the plan.
        plan_id (int): Foreign key to Plan record.
        phone_number (str): Phone number the plan is active on.
        valid_from (TIMESTAMP): Plan start/activation timestamp.
        valid_to (TIMESTAMP): Plan expiration/end timestamp.
        status (CurrentPlanStatus): Current status of the plan (active/expired/queued).
        plan (Plan): Relationship to the Plan object.
        user (User): Relationship to the User object.
    """
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
