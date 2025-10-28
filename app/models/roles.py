#models/roles.py
from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base

class Role(Base):
    __tablename__ = 'Roles'

    role_id = Column(Integer, primary_key=True)
    role_name = Column(String(50), nullable=False, unique=True)

    # Relationships
    # One Role can be linked to many Admins
    admins = relationship("Admin", back_populates="role")
    # One Role can have many permissions via RolePermission entries
    # role_permissions = relationship("RolePermission", back_populates="role")
