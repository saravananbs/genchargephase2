# models/permissions.py
from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from ..models.roles_permissions import RolePermission
from ..core.database import Base

class Permission(Base):
    """
    Permission/resource model defining granular access control rules.

    Attributes:
        permission_id (int): Primary key identifier for the permission.
        resource (str): Unique resource name that this permission applies to.
        read (bool): Indicates if read access is granted for this resource.
        write (bool): Indicates if write/create access is granted.
        delete (bool): Indicates if delete access is granted.
        edit (bool): Indicates if edit/update access is granted.
        role_permissions (List[RolePermission]): Relationship to RolePermission join records.
    """
    __tablename__ = 'Permissions'

    permission_id = Column(Integer, primary_key=True)
    resource = Column(String(100), nullable=False, unique=True)
    read = Column(Boolean, nullable=False, default=False)
    write = Column(Boolean, nullable=False, default=False)
    delete = Column(Boolean, nullable=False, default=False)
    edit = Column(Boolean, nullable=False, default=False)

    role_permissions = relationship(
        "RolePermission",
        back_populates="permission",
        foreign_keys=[RolePermission.permission_id]  # ← Critical fix
    )
    