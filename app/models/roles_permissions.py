#models/roles_permissions.py
from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from ..core.database import Base

class RolePermission(Base):
    __tablename__ = 'rolepermissions'

    id = Column(Integer, primary_key=True)

    # Foreign Keys
    role_id = Column(Integer, ForeignKey('Roles.role_id'), nullable=False)        # ← Fix
    permission_id = Column(Integer, ForeignKey('permissions.permission_id'), nullable=False)

    # Composite Unique Constraint for (role_id, permission_id)
    # __table_args__ = (
    #     UniqueConstraint('role_id', 'permission_id', name='_role_permission_uc'),
    # )

    # # Relationships
    # role = relationship("Role", back_populates="role_permissions")
    # permission = relationship("Permission", back_populates="role_permissions")

    