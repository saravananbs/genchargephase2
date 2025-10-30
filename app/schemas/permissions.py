from pydantic import BaseModel

class PermissionBase(BaseModel):
    resource: str
    read: bool = False
    write: bool = False
    delete: bool = False
    edit: bool = False

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(PermissionBase):
    pass

class PermissionOut(PermissionBase):
    permission_id: int

    class Config:
        from_attributes = True
