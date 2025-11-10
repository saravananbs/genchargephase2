#models/roles.py
from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from ..models.roles_permissions import RolePermission
from ..core.database import Base

class Role(Base):
    """
    Role model representing administrative role definitions with associated permissions.

    Attributes:
        role_id (int): Primary key identifier for the role.
        role_name (str): Unique name/label for the role.
        admins (List[Admin]): Relationship to Admin users with this role.
        role_permissions (List[RolePermission]): Relationship to permissions assigned to this role.
    """
    __tablename__ = 'Roles'

    role_id = Column(Integer, primary_key=True)
    role_name = Column(String(50), nullable=False, unique=True)

    admins = relationship("Admin", back_populates="role")
    
    role_permissions = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan",
        foreign_keys=[RolePermission.role_id]  
    )