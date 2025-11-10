# /schemas/offer.py
from pydantic import BaseModel, Field
from typing import Optional, Any, List
from datetime import datetime
from enum import Enum

class OfferTypeEnum(str, Enum):
    pass

class OfferStatus(str, Enum):
    """Enumeration for offer status values.
    
    Attributes:
        active (str): Offer is active and available.
        inactive (str): Offer is inactive and unavailable.
    """
    active = "active"
    inactive = "inactive"

class OfferBase(BaseModel):
    """Base schema for offer data.
    
    Attributes:
        offer_name (str): Name/title of the offer.
        offer_validity (Optional[int]): Validity period in days for the offer.
        offer_type_id (Optional[int]): ID of the offer type category.
        is_special (Optional[bool]): Whether this is a special/featured offer. Defaults to False.
        criteria (Optional[Any]): JSON criteria/conditions for offer eligibility.
        description (Optional[str]): Detailed description of the offer.
        status (OfferStatus): Current status (active/inactive). Defaults to active.
    """
    offer_name: str
    offer_validity: Optional[int] = None
    offer_type_id: Optional[int] = None
    is_special: Optional[bool] = False
    criteria: Optional[Any] = None
    description: Optional[str] = None
    status: OfferStatus = OfferStatus.active

class OfferCreate(OfferBase):
    """Schema for creating a new offer.
    
    Inherits all fields from OfferBase for offer creation.
    """
    pass

class OfferUpdate(BaseModel):
    """Schema for updating an existing offer with optional fields.
    
    Attributes:
        offer_name (Optional[str]): Updated offer name.
        offer_validity (Optional[int]): Updated validity period in days.
        offer_type_id (Optional[int]): Updated offer type ID.
        is_special (Optional[bool]): Updated special offer flag.
        criteria (Optional[Any]): Updated eligibility criteria.
        description (Optional[str]): Updated offer description.
        status (Optional[OfferStatus]): Updated status value.
    """
    offer_name: Optional[str] = None
    offer_validity: Optional[int] = None
    offer_type_id: Optional[int] = None
    is_special: Optional[bool] = None
    criteria: Optional[Any] = None
    description: Optional[str] = None
    status: Optional[OfferStatus] = None

class OfferTypeShort(BaseModel):
    """Shortened offer type information for nested responses.
    
    Attributes:
        offer_type_id (int): Unique identifier for offer type.
        offer_type_name (str): Display name of offer type.
    """
    offer_type_id: int
    offer_type_name: str
    class Config:
        from_attributes = True

class OfferResponse(OfferBase):
    """Complete offer response for admin/internal API endpoints.
    
    Includes offer identification, metadata, and nested offer type information.
    
    Attributes:
        offer_id (int): Unique identifier for the offer.
        created_by (Optional[int]): User ID of offer creator.
        created_at (datetime): Timestamp when offer was created.
        offer_type (Optional[OfferTypeShort]): Nested offer type details.
    """
    offer_id: int
    created_by: Optional[int]
    created_at: datetime
    offer_type: Optional[OfferTypeShort] = None

    class Config:
        from_attributes = True

class PublicOfferResponse(BaseModel):
    """Offer response for public/user-facing API endpoints.
    
    Excludes sensitive fields like created_by and internal metadata.
    
    Attributes:
        offer_id (int): Unique identifier for the offer.
        offer_name (str): Name of the offer.
        offer_validity (Optional[int]): Validity period in days.
        is_special (Optional[bool]): Whether offer is special/featured.
        criteria (Optional[Any]): Eligibility criteria for the offer.
        description (Optional[str]): Public description of the offer.
        offer_type (Optional[OfferTypeShort]): Nested offer type details.
    """
    offer_id: int
    offer_name: str
    offer_validity: Optional[int] = None
    is_special: Optional[bool] = None
    criteria: Optional[Any] = None
    description: Optional[str] = None
    offer_type: Optional[OfferTypeShort] = None

    class Config:
        from_attributes = True

class OfferFilter(BaseModel):
    """Filter and pagination parameters for offer list queries.
    
    Attributes:
        search (Optional[str]): Search text to filter offers by name or description.
        offer_type_id (Optional[int]): Filter by specific offer type ID.
        is_special (Optional[bool]): Filter by special offer flag.
        status (Optional[OfferStatus]): Filter by offer status (active/inactive).
        page (int): Page number for pagination (1-indexed). Minimum 1.
        limit (int): Items per page. Between 1 and 100. Defaults to 10.
        order_by (str): Field to order results by. Options: offer_id, offer_name, offer_validity, created_at.
        order_dir (str): Order direction (asc/desc). Defaults to desc.
    """
    search: Optional[str] = Field(None, description="Search in name/description")
    offer_type_id: Optional[int] = None
    is_special: Optional[bool] = None
    status: Optional[OfferStatus] = None
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    order_by: str = Field("offer_id", description="Field to order by (offer_id, offer_name, offer_validity, created_at)")
    order_dir: str = Field("desc", pattern="^(asc|desc)$")
