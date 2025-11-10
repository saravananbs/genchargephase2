# schemas/roles.py
from pydantic import BaseModel
from typing import List, Optional, Literal

class PermissionBase(BaseModel):
    """
    Schema representing permission information for role display.

    Attributes:
        permission_id (int): Unique permission identifier.
        resource (str): Resource this permission controls.
        read (bool): Read access granted.
        write (bool): Write/create access granted.
        delete (bool): Delete access granted.
        edit (bool): Edit/update access granted.
    """
    permission_id: int
    resource: str
    read: bool
    write: bool
    delete: bool
    edit: bool

    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    """
    Base schema for role data.

    Attributes:
        role_name (str): Unique name of the role.
    """
    role_name: str

class RoleCreate(RoleBase):
    """
    Schema for creating a new role with associated permissions.

    Inherits from RoleBase. Attributes:
        permission_ids (Optional[List[int]]): List of permission IDs to assign (default: empty).
    """
    permission_ids: Optional[List[int]] = []

class RoleUpdate(BaseModel):
    """
    Schema for updating role information and permissions.

    Attributes:
        role_name (Optional[str]): Updated role name.
        permission_ids (Optional[List[int]]): Updated list of permission IDs.
    """
    role_name: Optional[str] = None
    permission_ids: Optional[List[int]] = None

class RoleResponse(RoleBase):
    """
    Schema for returning role information with permissions in responses.

    Inherits from RoleBase. Attributes:
        role_id (int): Unique role identifier.
        permissions (List[PermissionBase]): List of permissions assigned to role.
    """
    role_id: int
    permissions: List[PermissionBase] = []

    class Config:
        from_attributes = True


class RoleListFilters(BaseModel):
    """
    Schema for filtering and paginating role list queries.

    Attributes:
        role_name (Optional[str]): Filter by role name (partial match).
        permission_resource (Optional[str]): Filter by permission resource.
        skip (int): Number of records to skip (default: 0).
        limit (int): Maximum records to return (default: 0 = all).
        sort_by (Optional[str]): Sort field (role_name).
        sort_order (Optional[str]): Sort direction (asc/desc, default: asc).
    """
    role_name: Optional[str] = None
    permission_resource: Optional[str] = None
    skip: int = 0
    limit: int = 0
    sort_by: Optional[Literal["role_name"]] = None
    sort_order: Optional[Literal["asc", "desc"]] = "asc"