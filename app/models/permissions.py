# models/permissions.py
from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from ..core.database import Base

class Permission(Base):
    __tablename__ = 'Permissions'

    permission_id = Column(Integer, primary_key=True)
    resource = Column(String(100), nullable=False, unique=True)
    read = Column(Boolean, nullable=False, default=False)
    write = Column(Boolean, nullable=False, default=False)
    delete = Column(Boolean, nullable=False, default=False)
    edit = Column(Boolean, nullable=False, default=False)

    # Relationships
    # One Permission can be linked to many roles via RolePermission entries
    # role_permissions = relationship("RolePermission", back_populates="permission")