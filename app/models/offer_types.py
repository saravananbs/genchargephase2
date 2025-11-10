from ..core.database import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

class OfferType(Base):
    """
    Offer type/category model representing types of promotional offers.

    Attributes:
        offer_type_id (int): Primary key identifier for the offer type.
        offer_type_name (str): Unique name/label for the offer type.
        offers (List[Offer]): Relationship to all Offer objects of this type.
    """
    __tablename__ = "OfferTypes"

    offer_type_id = Column(Integer, primary_key=True)
    offer_type_name = Column(String, unique=True, nullable=False)

    offers = relationship("Offer", back_populates="offer_type", passive_deletes=True)
