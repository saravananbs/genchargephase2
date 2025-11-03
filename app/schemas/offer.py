# /schemas/offer.py
from pydantic import BaseModel, Field
from typing import Optional, Any, List
from datetime import datetime
from enum import Enum

class OfferTypeEnum(str, Enum):
    # keep this only for typing in filters if needed
    pass

class OfferStatus(str, Enum):
    active = "active"
    inactive = "inactive"

# Base fields used for create/update
class OfferBase(BaseModel):
    offer_name: str
    offer_validity: Optional[int] = None
    offer_type_id: Optional[int] = None
    is_special: Optional[bool] = False
    criteria: Optional[Any] = None
    description: Optional[str] = None
    status: OfferStatus = OfferStatus.active

class OfferCreate(OfferBase):
    pass

class OfferUpdate(BaseModel):
    offer_name: Optional[str] = None
    offer_validity: Optional[int] = None
    offer_type_id: Optional[int] = None
    is_special: Optional[bool] = None
    criteria: Optional[Any] = None
    description: Optional[str] = None
    status: Optional[OfferStatus] = None

# Admin response: includes created_by and created_at and offer type name nested
class OfferTypeShort(BaseModel):
    offer_type_id: int
    offer_type_name: str
    class Config:
        from_attributes = True

class OfferResponse(OfferBase):
    offer_id: int
    created_by: Optional[int]
    created_at: datetime
    offer_type: Optional[OfferTypeShort] = None

    class Config:
        from_attributes = True

# User response: minimal public fields (no created_by or created_at)
class PublicOfferResponse(BaseModel):
    offer_id: int
    offer_name: str
    offer_validity: Optional[int] = None
    is_special: Optional[bool] = None
    criteria: Optional[Any] = None
    description: Optional[str] = None
    # include offer_type name for display if desired
    offer_type: Optional[OfferTypeShort] = None

    class Config:
        from_attributes = True

# Filter / pagination model
class OfferFilter(BaseModel):
    search: Optional[str] = Field(None, description="Search in name/description")
    offer_type_id: Optional[int] = None
    is_special: Optional[bool] = None
    status: Optional[OfferStatus] = None
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    order_by: str = Field("offer_id", description="Field to order by (offer_id, offer_name, offer_validity, created_at)")
    order_dir: str = Field("desc", pattern="^(asc|desc)$")
