from ..core.database import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

class PlanGroup(Base):
    __tablename__ = "PlanGroups"

    group_id = Column(Integer, primary_key=True)
    group_name = Column(String, unique=True, nullable=False)

    plans = relationship("Plan", back_populates="group", passive_deletes=True)
    
