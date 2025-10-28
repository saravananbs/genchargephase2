# crud/users.py
from sqlalchemy.orm import Session
from ..models.users import User
from ..schemas.users import UserCreate
from ..utils.security import get_password_hash
import datetime

def create_user(db: Session, user: UserCreate):
    db_user = User(
        name=user.name,
        email=user.email,
        phone_number=user.phone_number,
        referral_code=user.referral_code,
        referred_by=user.referred_by,
        user_type=user.user_type,
        status=user.status,
        wallet_balance=user.wallet_balance,
        created_at=user.created_at

    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_phone(db: Session, phone: str):
    return db.query(User).filter(User.phone_number == phone).first()

def update_user_status(db: Session, user_id: int, status: str):
    user = db.query(User).filter(User.user_id == user_id).first()
    if user:
        user.status = status
        db.commit()
        db.refresh(user)
    return user