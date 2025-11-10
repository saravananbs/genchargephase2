from pydantic import BaseModel

class PermissionBase(BaseModel):
    """
    Base schema for permission/resource access control data.

    Attributes:
        resource (str): Resource name that this permission controls.
        read (bool): Grant read access (default: False).
        write (bool): Grant write/create access (default: False).
        delete (bool): Grant delete access (default: False).
        edit (bool): Grant edit/update access (default: False).
    """
    resource: str
    read: bool = False
    write: bool = False
    delete: bool = False
    edit: bool = False

class PermissionCreate(PermissionBase):
    """
    Schema for creating new permissions (inherits all fields from PermissionBase).
    """
    pass

class PermissionUpdate(PermissionBase):
    """
    Schema for updating permission access controls (inherits all fields from PermissionBase).
    """
    pass

class PermissionOut(PermissionBase):
    """
    Schema for returning permission information in responses.

    Inherits from PermissionBase. Attributes:
        permission_id (int): Unique permission identifier.
    """
    permission_id: int

    class Config:
        from_attributes = True
