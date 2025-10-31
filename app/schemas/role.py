# schemas/roles.py
from pydantic import BaseModel
from typing import List, Optional

class PermissionBase(BaseModel):
    permission_id: int
    resource: str
    read: bool
    write: bool
    delete: bool
    edit: bool

    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    role_name: str

class RoleCreate(RoleBase):
    permission_ids: Optional[List[int]] = []

class RoleUpdate(BaseModel):
    role_name: Optional[str] = None
    permission_ids: Optional[List[int]] = None

class RoleResponse(RoleBase):
    role_id: int
    permissions: List[PermissionBase] = []

    class Config:
        from_attributes = True
