from pydantic import BaseModel

class RoleBase(BaseModel):
    role_name: str

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    role_name: str | None = None

class RoleOut(RoleBase):
    role_id: int

    class Config:
        from_attributes = True
