# models.py
from typing import Any, Optional, Annotated
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    GetJsonSchemaHandler,
)
from pydantic_core import core_schema
from datetime import datetime
from bson import ObjectId
from fastapi import Path


class PyObjectId(ObjectId):
    """Custom Pydantic type for MongoDB ObjectId serialization.
    
    Enables proper JSON serialization of MongoDB ObjectIds as strings while maintaining
    type safety in Pydantic models.
    """
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetJsonSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.is_instance_schema(ObjectId),
            serialization=core_schema.plain_serializer_function_ser_schema(lambda oid: str(oid)),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler) -> dict:
        json_schema = handler(core_schema)
        json_schema.update(type="string", format="objectid", example="507f1f77bcf86cd799439011")
        return json_schema


# --------------------------------------------------------------------------- #
#   Schemas
# --------------------------------------------------------------------------- #
class ContactFormBase(BaseModel):
    """Base schema for contact form data.
    
    Attributes:
        name (str): Name of the person submitting the form (1-255 characters).
        email (EmailStr): Valid email address of the contact.
        description (str): Contact message or inquiry description.
    """
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    description: str = Field(..., min_length=1)


class ContactFormCreate(ContactFormBase):
    """Schema for creating a new contact form submission.
    
    Inherits all fields from ContactFormBase for contact form creation.
    """
    pass


class ContactFormResponse(ContactFormBase):
    """Complete contact form response for API endpoints.
    
    Attributes:
        id (PyObjectId): MongoDB ObjectId stored as string in alias "_id".
        created_at (datetime): Timestamp when form was submitted.
        resolved (bool): Whether the contact form has been resolved. Defaults to False.
    """
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime
    resolved: bool = False

    class Config:
        # Pydantic v2 renamed this flag
        populate_by_name = True
        # Serialize ObjectId to string automatically
        json_encoders = {ObjectId: str}


class ContactFormUpdateResolved(BaseModel):
    """Schema for updating resolved status of a contact form.
    
    Attributes:
        resolved (bool): Whether the form submission has been resolved.
    """
    resolved: bool


class ContactFormFilter(BaseModel):
    """Filter and date range parameters for contact form list queries.
    
    Attributes:
        email (Optional[EmailStr]): Filter by specific email address.
        start_date (Optional[datetime]): Filter submissions from this date onwards.
        end_date (Optional[datetime]): Filter submissions up to this date.
        order (Optional[str]): Sort order direction (asc/desc). Defaults to desc.
    """
    email: Optional[EmailStr] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    order: Optional[str] = Field("desc", pattern="^(asc|desc)$")


ContactId = Annotated[
    PyObjectId,
    Path(
        description="MongoDB ObjectId (24-hex characters)",
        example="507f1f77bcf86cd799439011",
    ),
]