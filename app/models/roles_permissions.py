#models/roles_permissions.py
from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from ..core.database import Base

class RolePermission(Base):
    """
    Join table model associating roles with permissions (many-to-many relationship).

    Attributes:
        id (int): Primary key identifier.
        role_id (int): Foreign key to Role table.
        permission_id (int): Foreign key to Permission table.
        role (Role): Relationship to the Role object.
        permission (Permission): Relationship to the Permission object.
    """
    __tablename__ = 'RolePermissions'

    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey('Roles.role_id'), nullable=False)
    permission_id = Column(Integer, ForeignKey('Permissions.permission_id'), nullable=False)

    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")


    