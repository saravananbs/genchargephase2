from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AutoPayCredentialPaymentType(str, Enum):
    """Payment instruments supported for autopay credentials."""

    upi = "upi"
    bank = "bank"
    card = "card"


class AutoPayCredentialBase(BaseModel):
    payment_type: AutoPayCredentialPaymentType = Field(
        ..., description="Type of payment method stored for autopay"
    )
    credentials: dict[str, Any] = Field(
        ..., description="Opaque credentials payload for the payment method"
    )


class AutoPayCredentialUpsert(AutoPayCredentialBase):
    """Payload for creating or replacing autopay credentials."""


class AutoPayCredentialOut(AutoPayCredentialBase):
    id: int = Field(..., description="Primary key for the credential record")
    user_id: int = Field(..., description="Identifier of the credential owner")

    class Config:
        from_attributes = True
