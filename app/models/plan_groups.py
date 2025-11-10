from ..core.database import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

class PlanGroup(Base):
    """
    Plan group/category model representing logical groupings of plans.

    Attributes:
        group_id (int): Primary key identifier for the plan group.
        group_name (str): Unique name/label for the plan group.
        plans (List[Plan]): Relationship to all Plan objects in this group.
    """
    __tablename__ = "PlanGroups"

    group_id = Column(Integer, primary_key=True)
    group_name = Column(String, unique=True, nullable=False)

    plans = relationship("Plan", back_populates="group", passive_deletes=True)
    
