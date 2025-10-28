# crud/admins.py
from sqlalchemy.orm import Session
from ..models.admins import Admin
from ..schemas.admin import AdminBase
from ..utils.security import get_password_hash
import datetime

def create_admin(db: Session, admin: AdminBase):
    db_admin = Admin(
        name=admin.name,
        email=admin.email,
        phone_number=admin.phone_number,
        status=admin.status,
        created_at=admin.created_at,
        updated_at=admin.updated_at,
        role_id=admin.role_id
    )
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin

def get_admin_by_email(db: Session, email: str):
    return db.query(Admin).filter(Admin.email == email).first()

def get_admin_by_phone(db: Session, phone: str):
    return db.query(Admin).filter(Admin.phone_number == phone).first()

def update_admin_status(db: Session, admin_id: int, status: str):
    admin = db.query(Admin).filter(Admin.admin_id == admin_id).first()
    if admin:
        admin.status = status
        db.commit()
        db.refresh(admin)
    return admin
