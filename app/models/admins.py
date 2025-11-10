# models/admins.py
from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base
from sqlalchemy.sql import func

class Admin(Base):
    """
    Admin user account model representing administrative staff.

    Attributes:
        admin_id (int): Primary key identifier for the admin.
        name (str): Full name of the admin.
        email (str): Unique email address for the admin.
        phone_number (str): Unique phone number for the admin.
        created_at (TIMESTAMP): Timestamp of admin record creation.
        updated_at (TIMESTAMP): Timestamp of last admin record update.
        role_id (int): Foreign key reference to the Role table.
        role (Role): Relationship to the associated Role object.
    """
    __tablename__ = "Admins"

    admin_id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    phone_number = Column(String, unique=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    role_id = Column(Integer, ForeignKey("Roles.role_id"))
    role = relationship("Role", back_populates="admins")
