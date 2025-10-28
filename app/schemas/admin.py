from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr

# 1. Define the Enum for the 'status' field
class AdminStatus(str, Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    DELETED = "deleted"


# 2. Define the main Pydantic schema using minimal structure
class AdminBase(BaseModel):
    """
    Simplified Pydantic model for the Admin table, using type hints
    and the Enum for strict data validation.
    """
    admin_id: int
    name: str
    email: EmailStr
    phone_number: str
    status: AdminStatus
    role_id: int
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    class Config:
        """
        Minimal configuration to allow mapping from ORM objects
        and using string values for the Enum upon serialization.
        """
        from_attributes = True
        use_enum_values = True
