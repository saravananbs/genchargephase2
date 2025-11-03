from ..core.database import Base
from sqlalchemy import Column, Integer, ForeignKey, Boolean, JSON, Text, TIMESTAMP, func, String, Enum
from sqlalchemy.orm import relationship
import enum

class OfferStatus(enum.Enum):
    active = "active"
    inactive = "inactive"

class Offer(Base):
    __tablename__ = "Offers"

    offer_id = Column(Integer, primary_key=True)
    offer_name = Column(String, nullable=False)
    offer_validity = Column(Integer)
    offer_type_id = Column(
        Integer,
        ForeignKey("OfferTypes.offer_type_id", ondelete="SET NULL"),
        nullable=True
    )
    is_special = Column(Boolean, default=False)
    criteria = Column(JSON)
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    
    created_by = Column(Integer, nullable=True)
    
    status = Column(Enum(OfferStatus), nullable=False, default=OfferStatus.active)

    offer_type = relationship("OfferType", back_populates="offers")

