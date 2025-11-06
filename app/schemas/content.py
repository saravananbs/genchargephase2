from pydantic import BaseModel, Field, GetJsonSchemaHandler
from typing import Optional, List, Any
from datetime import datetime
from typing_extensions import Annotated
from bson import ObjectId
from pydantic_core import core_schema
from enum import Enum

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


class ContentBase(BaseModel):
    content_type: str = Field(..., example="article")
    title: str = Field(..., example="My First Post")
    body: Optional[str] = Field(None, example="This is the detailed content.")

class ContentCreateRequest(ContentBase):
    pass  # Form fields will be handled in router

class ContentUpdateRequest(BaseModel):
    content_type: Optional[str] = Field(None, example="article")
    title: Optional[str] = Field(None, example="Updated Title")
    body: Optional[str] = Field(None, example="Updated body")

class ContentResponseAdmin(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    content_type: str
    title: str
    body: Optional[str]
    image_url: Optional[str]
    image_filename: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime
    updated_by: int

    class Config:
        json_encoders = {object: str}
        populate_by_name = True

class ContentResponseUser(BaseModel):
    title: str
    body: Optional[str]
    image_url: Optional[str]

    class Config:
        populate_by_name = True

class PaginatedResponseAdmin(BaseModel):
    items: List[ContentResponseAdmin]
    total: int
    page: int
    size: int
    pages: int

class PaginatedResponseUser(BaseModel):
    items: List[ContentResponseUser]
    total: int
    page: int
    size: int
    pages: int

class ContentType(str, Enum):
    Landing_page_img1 = "Landing_page_img1"
    Landing_page_img2 = "Landing_page_img2"
    why_choose_us = "Why_Choose_us"
    FAQ = "FAQ"
    support_contact = "support_contact"

class CreateContentSchema(BaseModel):
    content_type: ContentType
    title: str
    body: Optional[str] = None

class UpdateContentSchema(CreateContentSchema):
    pass