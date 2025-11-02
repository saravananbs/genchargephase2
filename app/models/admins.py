# models/admins.py
from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base
from sqlalchemy.sql import func

class Admin(Base):
    __tablename__ = "Admins"

    admin_id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    phone_number = Column(String, unique=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    role_id = Column(Integer, ForeignKey("Roles.role_id"))
    role = relationship("Role", back_populates="admins")
