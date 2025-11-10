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
    """Base schema for content data.
    
    Attributes:
        content_type (str): Type of content (article, landing page, etc).
        title (str): Content title/heading.
        body (Optional[str]): Detailed content body/description.
    """
    content_type: str = Field(..., example="article")
    title: str = Field(..., example="My First Post")
    body: Optional[str] = Field(None, example="This is the detailed content.")

class ContentCreateRequest(ContentBase):
    """Schema for creating new content with image form fields handled in router.
    
    Inherits all fields from ContentBase for content creation.
    """
    pass  # Form fields will be handled in router

class ContentUpdateRequest(BaseModel):
    """Schema for updating existing content with optional fields.
    
    Attributes:
        content_type (Optional[str]): Updated content type.
        title (Optional[str]): Updated content title.
        body (Optional[str]): Updated content body.
    """
    content_type: Optional[str] = Field(None, example="article")
    title: Optional[str] = Field(None, example="Updated Title")
    body: Optional[str] = Field(None, example="Updated body")

class ContentResponseAdmin(BaseModel):
    """Complete content response for admin/internal API endpoints.
    
    Includes full metadata including creator info, timestamps, and image URLs.
    
    Attributes:
        id (PyObjectId): MongoDB ObjectId stored as string in alias "_id".
        content_type (str): Type of content.
        title (str): Content title.
        body (Optional[str]): Content body/description.
        image_url (Optional[str]): Public URL of the uploaded image.
        image_filename (Optional[str]): Filename of the uploaded image.
        created_by (int): User ID of content creator.
        created_at (datetime): Timestamp when content was created.
        updated_at (datetime): Timestamp when content was last updated.
        updated_by (int): User ID of last updater.
    """
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
    """Content response for public/user-facing API endpoints.
    
    Excludes sensitive fields like creator info and internal timestamps.
    
    Attributes:
        title (str): Content title.
        body (Optional[str]): Content body/description.
        image_url (Optional[str]): Public URL of the content image.
    """
    title: str
    body: Optional[str]
    image_url: Optional[str]

    class Config:
        populate_by_name = True


class PaginatedResponseAdmin(BaseModel):
    """Paginated response for admin content list queries.
    
    Attributes:
        items (List[ContentResponseAdmin]): List of admin content response objects.
        total (int): Total number of content items matching query.
        page (int): Current page number.
        size (int): Items per page.
        pages (int): Total number of pages.
    """
    items: List[ContentResponseAdmin]
    total: int
    page: int
    size: int
    pages: int

class PaginatedResponseUser(BaseModel):
    """Paginated response for public content list queries.
    
    Attributes:
        items (List[ContentResponseUser]): List of user-facing content response objects.
        total (int): Total number of content items matching query.
        page (int): Current page number.
        size (int): Items per page.
        pages (int): Total number of pages.
    """
    items: List[ContentResponseUser]
    total: int
    page: int
    size: int
    pages: int

class ContentType(str, Enum):
    """Enumeration for content type categories.
    
    Attributes:
        Landing_page_img1 (str): First landing page image.
        Landing_page_img2 (str): Second landing page image.
        why_choose_us (str): Why choose us content section.
        FAQ (str): Frequently asked questions content.
        support_contact (str): Support contact information.
    """
    Landing_page_img1 = "Landing_page_img1"
    Landing_page_img2 = "Landing_page_img2"
    why_choose_us = "Why_Choose_us"
    FAQ = "FAQ"
    support_contact = "support_contact"

class CreateContentSchema(BaseModel):
    """Schema for creating new content with required fields.
    
    Attributes:
        content_type (ContentType): Type of content from enum.
        title (str): Content title.
        body (Optional[str]): Content body/description.
    """
    content_type: ContentType
    title: str
    body: Optional[str] = None

class UpdateContentSchema(CreateContentSchema):
    """Schema for updating existing content.
    
    Inherits all fields from CreateContentSchema for content updates.
    """
    pass