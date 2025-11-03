from pydantic import BaseModel, Field
from typing import Optional, List

class OfferTypeBase(BaseModel):
    offer_type_name: str = Field(..., example="Festive Offer")

class OfferTypeCreate(OfferTypeBase):
    pass

class OfferTypeUpdate(BaseModel):
    offer_type_name: Optional[str] = Field(None, example="New Year Offer")

class OfferTypeOut(OfferTypeBase):
    offer_type_id: int

    class Config:
        from_attributes = True

class OfferTypeFilter(BaseModel):
    search: Optional[str] = None
    order_by: Optional[str] = Field("offer_type_id", description="Field to order by")
    order_dir: Optional[str] = Field("asc", description="asc or desc")
    limit: Optional[int] = Field(10, ge=1, le=100)
    offset: Optional[int] = Field(0, ge=0)
