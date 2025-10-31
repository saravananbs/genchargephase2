#models/roles.py
from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from ..models.roles_permissions import RolePermission
from ..core.database import Base

class Role(Base):
    __tablename__ = 'Roles'

    role_id = Column(Integer, primary_key=True)
    role_name = Column(String(50), nullable=False, unique=True)

    admins = relationship("Admin", back_populates="role")
    
    # Reverse relationship: explicitly specify foreign_keys
    role_permissions = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan",
        foreign_keys=[RolePermission.role_id]  # ← Also good to specify
    )