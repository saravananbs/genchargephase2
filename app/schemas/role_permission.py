from pydantic import BaseModel

class RolePermissionCreate(BaseModel):
    role_id: int
    permission_id: int

class RolePermissionOut(RolePermissionCreate):
    id: int

    class Config:
        from_attributes = True
    