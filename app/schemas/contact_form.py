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
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    description: str = Field(..., min_length=1)


class ContactFormCreate(ContactFormBase):
    pass


class ContactFormResponse(ContactFormBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime
    resolved: bool = False

    class Config:
        # Pydantic v2 renamed this flag
        populate_by_name = True
        # Serialize ObjectId to string automatically
        json_encoders = {ObjectId: str}


class ContactFormUpdateResolved(BaseModel):
    resolved: bool


class ContactFormFilter(BaseModel):
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