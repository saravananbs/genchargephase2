#models/roles_permissions.py
from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from ..core.database import Base

class RolePermission(Base):
    __tablename__ = 'RolePermissions'

    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey('Roles.role_id'), nullable=False)
    permission_id = Column(Integer, ForeignKey('Permissions.permission_id'), nullable=False)

    # Forward relationships
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")


    