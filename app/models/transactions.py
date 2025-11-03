from ..core.database import Base
from sqlalchemy import Column, Integer, Numeric, Enum, String, func, TIMESTAMP
from sqlalchemy.orm import relationship
import enum

class TransactionCategory(enum.Enum):
    wallet = "wallet"
    service = "service"

class TransactionType(enum.Enum):
    credit = "credit"
    debit = "debit"


class ServiceType(enum.Enum):
    prepaid = "prepaid"
    postpaid = "postpaid"


class TransactionSource(enum.Enum):
    recharge = "recharge"
    wallet_topup = "wallet_topup"
    refund = "refund"
    referral_reward = "referral_reward"
    autopay = "autopay"


class TransactionStatus(enum.Enum):
    success = "success"
    failed = "failed"
    pending = "pending"


class PaymentMethod(enum.Enum):
    UPI = "UPI"
    Card = "Card"
    NetBanking = "NetBanking"
    Wallet = "Wallet"

class Transaction(Base):
    __tablename__ = "Transactions"

    txn_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)
    
    category = Column(Enum(TransactionCategory), nullable=False)
    txn_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    service_type = Column(Enum(ServiceType))
    
    plan_id = Column(Integer, nullable=True)
    offer_id = Column(Integer, nullable=True)
    
    from_phone_number = Column(String)
    to_phone_number = Column(String)
    source = Column(Enum(TransactionSource), nullable=False)
    status = Column(Enum(TransactionStatus), nullable=False)
    payment_method = Column(Enum(PaymentMethod))
    payment_transaction_id = Column(String)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
