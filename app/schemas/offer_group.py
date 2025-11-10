from pydantic import BaseModel, Field
from typing import Optional, List

class OfferTypeBase(BaseModel):
    """Base schema for offer type data.
    
    Attributes:
        offer_type_name (str): Name of the offer type category (e.g., Festive Offer).
    """
    offer_type_name: str = Field(..., example="Festive Offer")

class OfferTypeCreate(OfferTypeBase):
    """Schema for creating a new offer type.
    
    Inherits all fields from OfferTypeBase for offer type creation.
    """
    pass

class OfferTypeUpdate(BaseModel):
    """Schema for updating an existing offer type with optional fields.
    
    Attributes:
        offer_type_name (Optional[str]): Updated name of the offer type.
    """
    offer_type_name: Optional[str] = Field(None, example="New Year Offer")

class OfferTypeOut(OfferTypeBase):
    """Complete offer type response for API endpoints.
    
    Attributes:
        offer_type_id (int): Unique identifier for the offer type.
    """
    offer_type_id: int

    class Config:
        from_attributes = True

class OfferTypeFilter(BaseModel):
    """Filter and pagination parameters for offer type list queries.
    
    Attributes:
        search (Optional[str]): Search text to filter by offer type name.
        order_by (Optional[str]): Field to order results by. Defaults to offer_type_id.
        order_dir (Optional[str]): Order direction (asc/desc). Defaults to asc.
        limit (Optional[int]): Maximum items to return. Between 1-100. Defaults to 10.
        offset (Optional[int]): Number of items to skip for pagination. Defaults to 0.
    """
    search: Optional[str] = None
    order_by: Optional[str] = Field("offer_type_id", description="Field to order by")
    order_dir: Optional[str] = Field("asc", description="asc or desc")
    limit: Optional[int] = Field(10, ge=1, le=100)
    offset: Optional[int] = Field(0, ge=0)
