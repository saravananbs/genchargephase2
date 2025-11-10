from ..core.database import Base
from sqlalchemy import Column, Integer, ForeignKey, Boolean, JSON, Text, TIMESTAMP, func, String, Enum
from sqlalchemy.orm import relationship
import enum

class OfferStatus(enum.Enum):
    """
    Enumeration of offer status values.

    Values:
        active: Offer is currently active and available.
        inactive: Offer is inactive and not available.
    """
    active = "active"
    inactive = "inactive"

class Offer(Base):
    """
    Promotional offer model representing marketing offers for users.

    Attributes:
        offer_id (int): Primary key identifier for the offer.
        offer_name (str): Name/title of the offer.
        offer_validity (int): Validity period of the offer in days.
        offer_type_id (int): Foreign key to OfferType.
        is_special (bool): Flag indicating if this is a special promotional offer.
        criteria (JSON): JSON criteria/conditions for offer eligibility.
        description (str): Detailed description of the offer.
        created_at (TIMESTAMP): Timestamp when offer was created.
        created_by (int): Admin user ID who created the offer.
        status (OfferStatus): Offer status (active or inactive).
        offer_type (OfferType): Relationship to the OfferType object.
    """
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

