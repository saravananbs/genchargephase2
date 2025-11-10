from ..core.database import Base
from sqlalchemy import Column, Integer, Numeric, Enum, String, func, TIMESTAMP
from sqlalchemy.orm import relationship
import enum

class TransactionCategory(enum.Enum):
    """
    Enumeration of transaction category values.

    Values:
        wallet: Transaction involving wallet balance changes.
        service: Transaction involving service usage/purchase.
    """
    wallet = "wallet"
    service = "service"

class TransactionType(enum.Enum):
    """
    Enumeration of transaction type values.

    Values:
        credit: Money added to wallet or account.
        debit: Money deducted from wallet or account.
    """
    credit = "credit"
    debit = "debit"


class ServiceType(enum.Enum):
    """
    Enumeration of service type values.

    Values:
        prepaid: Prepaid service model.
        postpaid: Postpaid service model.
    """
    prepaid = "prepaid"
    postpaid = "postpaid"


class TransactionSource(enum.Enum):
    """
    Enumeration of transaction source values indicating where transaction originated.

    Values:
        recharge: Direct recharge transaction.
        wallet_topup: Wallet top-up by user.
        refund: Refund of previous transaction.
        referral_reward: Reward from successful referral.
        autopay: Automatic recurring payment.
    """
    recharge = "recharge"
    wallet_topup = "wallet_topup"
    refund = "refund"
    referral_reward = "referral_reward"
    autopay = "autopay"


class TransactionStatus(enum.Enum):
    """
    Enumeration of transaction status values.

    Values:
        success: Transaction completed successfully.
        failed: Transaction failed to complete.
        pending: Transaction is in progress/pending completion.
    """
    success = "success"
    failed = "failed"
    pending = "pending"


class PaymentMethod(enum.Enum):
    """
    Enumeration of payment method values for transactions.

    Values:
        UPI: Unified Payments Interface.
        Card: Credit or debit card.
        NetBanking: Online net banking transfer.
        Wallet: Internal wallet balance.
    """
    UPI = "UPI"
    Card = "Card"
    NetBanking = "NetBanking"
    Wallet = "Wallet"

class Transaction(Base):
    """
    Transaction model tracking all financial and service transactions.

    Attributes:
        txn_id (int): Primary key transaction identifier.
        user_id (int): ID of the user involved in transaction.
        category (TransactionCategory): Category of transaction (wallet/service).
        txn_type (TransactionType): Type of transaction (credit/debit).
        amount (Numeric): Transaction amount in currency.
        service_type (ServiceType): Service type if applicable (prepaid/postpaid).
        plan_id (int): ID of plan if associated with transaction.
        offer_id (int): ID of offer if associated with transaction.
        from_phone_number (str): Source phone number for transaction.
        to_phone_number (str): Destination phone number for transaction.
        source (TransactionSource): Origin/source of the transaction.
        status (TransactionStatus): Status of the transaction.
        payment_method (PaymentMethod): Payment method used.
        payment_transaction_id (str): External payment gateway transaction ID.
        created_at (TIMESTAMP): Timestamp when transaction was created.
    """
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
