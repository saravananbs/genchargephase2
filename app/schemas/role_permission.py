from pydantic import BaseModel

class RolePermissionCreate(BaseModel):
    """Schema for associating a permission with a role.
    
    Attributes:
        role_id (int): ID of the role.
        permission_id (int): ID of the permission to associate.
    """
    role_id: int
    permission_id: int

class RolePermissionOut(RolePermissionCreate):
    """Complete role-permission association response.
    
    Includes the association ID and inherits fields from RolePermissionCreate.
    
    Attributes:
        id (int): Unique identifier for the role-permission association.
    """
    id: int

    class Config:
        from_attributes = True
    