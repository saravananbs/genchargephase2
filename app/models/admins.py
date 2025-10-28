# models/admins.py
from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum

class AdminStatus(enum.Enum):
    active = "active"
    blocked = "blocked"
    deleted = "deleted"

class Admin(Base):
    __tablename__ = "Admins"

    admin_id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    phone_number = Column(String, unique=True)
    status = Column(Enum(AdminStatus))
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    role_id = Column(Integer, ForeignKey("Roles.role_id"))

    # ← ADD THIS LINE
    role = relationship("Role", back_populates="admins")