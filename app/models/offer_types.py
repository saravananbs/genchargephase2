from ..core.database import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

class OfferType(Base):
    __tablename__ = "OfferTypes"

    offer_type_id = Column(Integer, primary_key=True)
    offer_type_name = Column(String, unique=True, nullable=False)

    offers = relationship("Offer", back_populates="offer_type", passive_deletes=True)
