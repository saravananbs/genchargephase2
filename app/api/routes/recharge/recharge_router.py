from fastapi import APIRouter, Depends, HTTPException, status, Query, Security
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, asc, and_, or_, func, TIMESTAMP
from typing import List, Optional, Literal
from datetime import datetime, timedelta
from decimal import Decimal
import enum
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.sql import expression

# Assuming these are already defined in your models file
from ....models.users import User, UserType, UserStatus
from ....models.plans import Plan, PlanType, PlanStatus
from ....models.offers import Offer, OfferStatus
from ....models.transactions import Transaction, TransactionCategory, TransactionType, TransactionSource, TransactionStatus, PaymentMethod, ServiceType
from ....models.current_active_plans import CurrentActivePlan, CurrentPlanStatus
from ....core.database import get_db
from ....schemas.users import UserResponse
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes

router = APIRouter()

# ====================== Pydantic Schemas ======================

# --- Plan ---
class PlanOut(BaseModel):
    plan_id: int
    plan_name: str
    validity: Optional[int] = None
    most_popular: bool = False
    plan_type: PlanType
    group_id: Optional[int] = None
    description: Optional[str] = None
    criteria: Optional[dict] = None
    status: PlanStatus
    created_at: datetime

    class Config:
        from_attributes = True


class PlanListResponse(BaseModel):
    plans: List[PlanOut]
    total: int
    page: int
    size: int
    pages: int


# --- Offer ---
class OfferOut(BaseModel):
    offer_id: int
    offer_name: str
    offer_validity: Optional[int] = None
    offer_type_id: Optional[int] = None
    is_special: bool = False
    criteria: Optional[dict] = None
    description: Optional[str] = None
    status: OfferStatus
    created_at: datetime

    class Config:
        from_attributes = True


# --- Current Active Plan ---
class CurrentActivePlanOut(BaseModel):
    id: int
    user_id: int
    plan_id: int
    phone_number: str
    valid_from: datetime
    valid_to: datetime
    status: CurrentPlanStatus
    plan: PlanOut

    class Config:
        from_attributes = True

class PlanListResponse(BaseModel):
    plans: List[CurrentActivePlanOut]      # whatever your out-model is
    total: int
    page: int
    size: int
    pages: int


# --- Transaction ---
class TransactionOut(BaseModel):
    txn_id: int
    user_id: Optional[int] = None
    category: TransactionCategory
    txn_type: TransactionType
    amount: Decimal
    service_type: Optional[ServiceType] = None
    plan_id: Optional[int] = None
    offer_id: Optional[int] = None
    from_phone_number: Optional[str] = None
    to_phone_number: Optional[str] = None
    source: TransactionSource
    status: TransactionStatus
    payment_method: Optional[PaymentMethod] = None
    payment_transaction_id: Optional[str] = None
    created_at: datetime
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True

class TransactionListResponse(BaseModel):
    transactions: List[TransactionOut]  # your Transaction Pydantic model
    total: int
    page: int
    size: int
    pages: int

# --- Request Models ---
class RechargeRequest(BaseModel):
    phone_number: str = Field(..., description="Target mobile number for recharge")
    plan_id: int = Field(..., description="ID of the plan to subscribe")
    offer_id: Optional[int] = Field(None, description="Optional offer to apply")
    payment_method: PaymentMethod = Field(..., description="Payment method used")
    source: TransactionSource = Field(
        ..., description="Source of the transaction (recharge, autopay, etc.)"
    )
    activation_mode: Literal["activate", "queue"] = "activate"

    


class WalletTopupRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Amount to top-up")
    phone_number: Optional[str] = Field(
        None, description="If omitted, top-up the authenticated user's wallet"
    )
    payment_method: PaymentMethod = Field(..., description="Payment method used")

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v


class ApplyOfferRequest(BaseModel):
    offer_id: int = Field(..., description="ID of the offer")
    plan_id: int = Field(..., description="ID of the plan")
    phone_number: str = Field(..., description="Target mobile number")

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 10:
            raise ValueError("Phone number must be exactly 10 digits")
        return v


# ====================== Helper Functions ======================

def evaluate_criteria(criteria: dict, context: dict) -> bool:
    """Evaluate plan/offer criteria against user/transaction context"""
    if not criteria or "conditions" not in criteria:
        return True

    conditions = criteria["conditions"]

    # Time validity
    now = datetime.now()
    valid_from = conditions.get("valid_from")
    valid_to = conditions.get("valid_to")
    if valid_from and datetime.fromisoformat(valid_from.replace("Z", "+00:00")) > now:
        return False
    if valid_to and datetime.fromisoformat(valid_to.replace("Z", "+00:00")) < now:
        return False

    # Min amount
    if "min_amount" in conditions and context.get("amount", 0) < conditions["min_amount"]:
        return False

    # User type
    if "user_type" in conditions and context.get("user_type") not in conditions["user_type"]:
        return False

    # New user
    if conditions.get("is_new_user") and not context.get("is_new_user"):
        return False

    # Applicable sources
    if "applicable_sources" in conditions and context.get("source") not in conditions["applicable_sources"]:
        return False

    # Valid plan groups (if plan has group)
    if "valid_plan_groups" in conditions:
        plan_group = context.get("plan_group_name")
        if not plan_group or plan_group not in conditions["valid_plan_groups"]:
            return False

    return True


def calculate_reward(offer_criteria: dict, plan_amount: Decimal) -> tuple[Decimal, Decimal]:
    """
    Returns: (discount_amount, cashback_amount)
    """
    discount = Decimal('0')
    cashback = Decimal('0')

    conditions = offer_criteria.get("conditions", {})
    rewards = offer_criteria.get("rewards", {})

    # Example: flat discount
    if rewards.get("discount_type") == "flat":
        discount = Decimal(str(rewards["discount_value"]))

    # Example: cashback
    if rewards.get("cashback_type") == "flat":
        cashback = Decimal(str(rewards["cashback_value"]))

    # Cap discount
    discount = min(discount, plan_amount)

    return discount, cashback

def _decide_plan_status(
    has_active: bool,
    force_queue: bool,
    force_activate: bool,
) -> CurrentPlanStatus:
    """
    * If the caller explicitly says `queue=True` → queued
    * If the caller explicitly says `queue=False` → try to activate
        - activate only if there is **no** active plan
        - otherwise queue
    """
    if force_queue:
        return CurrentPlanStatus.queued
    if not has_active or force_activate:
        return CurrentPlanStatus.active
    return CurrentPlanStatus.queued

async def count_active_plans(db: AsyncSession, user_id: int, phone: str) -> int:
    result = await db.execute(
        select(func.count()).where(
            CurrentActivePlan.user_id == user_id,
            CurrentActivePlan.phone_number == phone,
            CurrentActivePlan.status == CurrentPlanStatus.active
        )
    )
    return result.scalar_one()

# === Helper: Async version of get_user_by_phone ===
async def get_user_by_phone(db: AsyncSession, phone: str) -> User:
    result = await db.execute(select(User).where(User.phone_number == phone))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with phone {phone} not found")
    return user

# === Helper: Async version of activate_queued_plan ===
async def activate_queued_plan(db: AsyncSession, user_id: int, phone_number: str):
    """Check and activate any queued plan when current expires"""
    now = datetime.now()

    # Expire any active plans that have valid_to < now
    active_plans_result = await db.execute(
        select(CurrentActivePlan).where(
            CurrentActivePlan.user_id == user_id,
            CurrentActivePlan.phone_number == phone_number,
            CurrentActivePlan.status == CurrentPlanStatus.active,
            CurrentActivePlan.valid_to < now
        )
    )
    active_plans = active_plans_result.scalars().all()
    for plan in active_plans:
        plan.status = CurrentPlanStatus.expired
        db.add(plan)

    # Find the earliest queued plan where valid_from <= now
    queued_result = await db.execute(
        select(CurrentActivePlan)
        .where(
            CurrentActivePlan.user_id == user_id,
            CurrentActivePlan.phone_number == phone_number,
            CurrentActivePlan.status == CurrentPlanStatus.queued
        )
        .order_by(CurrentActivePlan.valid_from)
    )
    queued = queued_result.scalars().first()

    if queued and queued.valid_from <= now:
        queued.status = CurrentPlanStatus.active
        db.add(queued)

    await db.commit()

# ====================== User Endpoints ======================
@router.post("/subscribe", response_model=TransactionOut)
async def subscribe_plan(
    request: RechargeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"], use_cache=False)
):
    # Resolve target user
    target_phone = request.phone_number
    target_user = await get_user_by_phone(db, target_phone)

    # Validate plan
    plan_result = await db.execute(
        select(Plan).options(selectinload(Plan.group)).where(Plan.plan_id == request.plan_id, Plan.status == PlanStatus.active)
    )
    plan = plan_result.scalars().first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found or inactive")
    offer_result = await db.execute(
        select(Offer).options(selectinload(Offer.offer_type)).where(Offer.offer_id == request.offer_id, Offer.status == OfferStatus.active)
    )
    offer = offer_result.scalars().first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found or inactive")

    # Build context for criteria
    context = {
        "amount": Decimal('0'),
        "user_type": target_user.user_type.value,
        "is_new_user": False,
        "source": request.source.value,
        "plan_group_name": None
    }

    # Fetch plan group name if exists
    if plan.group:
        context["plan_group_name"] = plan.group.group_name

    # Determine amount from criteria or raise error
    plan_amount = Decimal('0')
    if plan.criteria and "conditions" in plan.criteria and "min_amount" in plan.criteria["conditions"]:
        plan_amount = Decimal(str(plan.criteria["conditions"]["min_amount"]))
    else:
        raise HTTPException(status_code=400, detail="Plan price not defined")
    context["amount"] = plan_amount

    # Validate plan criteria
    if not evaluate_criteria(plan.criteria, context):
        raise HTTPException(status_code=400, detail="User does not meet plan criteria")

    # Apply offer if provided
    discount_amount = Decimal('0')
    cashback_amount = Decimal('0')
    applied_offer = None

    if request.offer_id:
        offer_result = await db.execute(
            select(Offer).where(Offer.offer_id == request.offer_id, Offer.status == OfferStatus.active)
        )
        offer = offer_result.scalars().first()
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found or inactive")
        if not evaluate_criteria(offer.criteria, context):
            raise HTTPException(status_code=400, detail="Offer criteria not satisfied")

        discount_amount, cashback_amount = calculate_reward(offer.criteria, plan_amount)
        applied_offer = offer

    # === Payment deduction ===
    total_deduct = plan_amount - discount_amount  # Only discount reduces payment

    # Check wallet balance if paying via wallet
    if request.payment_method == PaymentMethod.Wallet:
        if current_user.user_id == target_user.user_id and current_user.wallet_balance < total_deduct:
            raise HTTPException(status_code=400, detail="Insufficient wallet balance")
        current_user.wallet_balance -= total_deduct

    # Activate queued plans first
    await activate_queued_plan(db, target_user.user_id, target_phone)

    # Determine validity
    valid_from = datetime.now()
    valid_to = valid_from + timedelta(days=plan.validity) if plan.validity else valid_from + timedelta(days=30)

    # Check if any active plan exists
    has_active_result = await db.execute(
        select(CurrentActivePlan).where(
            CurrentActivePlan.user_id == target_user.user_id,
            CurrentActivePlan.phone_number == target_phone,
            CurrentActivePlan.status == CurrentPlanStatus.active
        )
    )
    has_active = has_active_result.scalars().first() is not None
    plan_status = CurrentPlanStatus.queued if has_active else CurrentPlanStatus.active

    # Create active plan entry
    active_plan = CurrentActivePlan(
        user_id=target_user.user_id,
        plan_id=plan.plan_id,
        phone_number=target_phone,
        valid_from=valid_from,
        valid_to=valid_to,
        status=plan_status
    )
    db.add(active_plan)

    # Create transaction
    txn = Transaction(
        user_id=current_user.user_id,
        category=TransactionCategory.service,
        txn_type=TransactionType.debit,
        amount=plan_amount,
        service_type=ServiceType.prepaid if plan.plan_type == PlanType.prepaid else ServiceType.postpaid,
        plan_id=plan.plan_id,
        offer_id=applied_offer.offer_id if applied_offer else None,
        from_phone_number=current_user.phone_number,
        to_phone_number=target_phone,
        source=request.source,
        status=TransactionStatus.success,
        payment_method=request.payment_method,
        payment_transaction_id=f"PYMT_{datetime.now().timestamp()}",
        created_at=datetime.now()
    )
    db.add(txn)

    # Credit reward if cashback
    if cashback_amount > 0:
        reward_txn = Transaction(
            user_id=target_user.user_id,
            category=TransactionCategory.wallet,
            txn_type=TransactionType.credit,
            amount=cashback_amount,
            source=TransactionSource.offer_cashback,
            status=TransactionStatus.success,
            created_at=datetime.now()
        )
        db.add(reward_txn)
        target_user.wallet_balance += cashback_amount

    await db.commit()
    await db.refresh(txn)
    return txn


@router.post("/wallet/topup", response_model=TransactionOut)
async def wallet_topup(
    request: WalletTopupRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"], use_cache=False)
):
    target_phone = request.phone_number or current_user.phone_number
    target_user = await get_user_by_phone(db, target_phone)

    if request.payment_method == PaymentMethod.Wallet and current_user.wallet_balance < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient wallet balance")

    if request.payment_method == PaymentMethod.Wallet:
        current_user.wallet_balance -= request.amount

    target_user.wallet_balance += request.amount

    txn = Transaction(
        user_id=current_user.user_id,
        category=TransactionCategory.wallet,
        txn_type=TransactionType.credit,
        amount=request.amount,
        from_phone_number=current_user.phone_number,
        to_phone_number=target_phone,
        source=TransactionSource.wallet_topup,
        status=TransactionStatus.success,
        payment_method=request.payment_method,
        payment_transaction_id=f"TOPUP_{datetime.now().timestamp()}",
        created_at=datetime.now()
    )
    db.add(txn)
    await db.commit()
    await db.refresh(txn)
    return txn


@router.get("/my/plans", response_model=List[CurrentActivePlanOut])
async def get_my_active_plans(
    status: Optional[CurrentPlanStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"], use_cache=False)
):
    query = select(CurrentActivePlan).options(selectinload(CurrentActivePlan.plan)).where(
        CurrentActivePlan.user_id == current_user.user_id
    )
    if status:
        query = query.where(CurrentActivePlan.status == status)

    result = await db.execute(query)
    plans = result.scalars().all()
    return plans


@router.get("/my/transactions")
async def get_my_transactions(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    category: Optional[TransactionCategory] = None,
    txn_type: Optional[TransactionType] = None,
    status: Optional[TransactionStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"], use_cache=False)
):
    query = select(Transaction).where(Transaction.user_id == current_user.user_id)
    if category:
        query = query.where(Transaction.category == category)
    if txn_type:
        query = query.where(Transaction.txn_type == txn_type)
    if status:
        query = query.where(Transaction.status == status)

    # Count total
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    # Paginated results
    result = await db.execute(
        query.order_by(desc(Transaction.created_at))
        .offset((page - 1) * size)
        .limit(size)
    )
    transactions = result.scalars().all()

    return {
        "transactions": transactions,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


# ====================== Admin Endpoints ======================
@router.get("/admin/active-plans", response_model=PlanListResponse)
async def admin_list_active_plans(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(10, ge=1, le=500, description="Items per page (max 500)"),
    phone_number: Optional[str] = Query(None, description="Filter by phone"),
    plan_id: Optional[int] = Query(None, description="Filter by plan_id"),
    status: Optional[CurrentPlanStatus] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),               # <-- async DB
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes,
                         scopes=["Recharge:read"], use_cache=False),
):
    """
    Return **all** active-plan rows that match the optional filters,
    paginated, sorted by `valid_from` descending.
    """

    # --------------------------------------------------------------
    # 2. Build the base SELECT with eager loads
    # --------------------------------------------------------------
    stmt = select(CurrentActivePlan).options(
        selectinload(CurrentActivePlan.plan),
        selectinload(CurrentActivePlan.user)
    )

    # --------------------------------------------------------------
    # 3. Apply filters (only if the param is supplied)
    # --------------------------------------------------------------
    if phone_number:
        stmt = stmt.where(CurrentActivePlan.phone_number == phone_number)
    if plan_id:
        stmt = stmt.where(CurrentActivePlan.plan_id == plan_id)
    if status:
        stmt = stmt.where(CurrentActivePlan.status == status)

    # --------------------------------------------------------------
    # 4. TOTAL COUNT (for pagination metadata)
    # --------------------------------------------------------------
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    # --------------------------------------------------------------
    # 5. Pagination + sorting
    # --------------------------------------------------------------
    stmt = stmt.order_by(desc(CurrentActivePlan.valid_from))
    stmt = stmt.offset((page - 1) * size).limit(size)

    result = await db.execute(stmt)
    plans = result.scalars().all()

    # --------------------------------------------------------------
    # 6. Build response
    # --------------------------------------------------------------
    return PlanListResponse(
        plans=plans,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/admin/transactions", response_model=TransactionListResponse)
async def admin_list_transactions(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=0, le=10000, description="0 = return ALL rows"),
    user_id: Optional[int] = None,
    phone_number: Optional[str] = None,
    category: Optional[TransactionCategory] = None,
    status: Optional[TransactionStatus] = None,
    db: AsyncSession = Depends(get_db),          # async session
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Recharge:read"], use_cache=False),
):
    """
    Return **all** matching transactions (size=0 → everything).
    User data is attached **without adding a relationship** to Transaction.
    """
    # --------------------------------------------------------------
    # Base SELECT – only Transaction columns
    # --------------------------------------------------------------
    stmt = select(Transaction)

    # --------------------------------------------------------------
    # Filters
    # --------------------------------------------------------------
    if user_id:
        stmt = stmt.where(Transaction.user_id == user_id)
    if phone_number:
        stmt = stmt.where(
            or_(
                Transaction.from_phone_number == phone_number,
                Transaction.to_phone_number == phone_number,
            )
        )
    if category:
        stmt = stmt.where(Transaction.category == category)
    if status:
        stmt = stmt.where(Transaction.status == status)

    # --------------------------------------------------------------
    # TOTAL count (filtered)
    # --------------------------------------------------------------
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()

    # --------------------------------------------------------------
    # “Return everything” shortcut
    # --------------------------------------------------------------
    if size == 0:
        stmt = stmt.order_by(desc(Transaction.created_at))
        result = await db.execute(stmt)
        txns = result.scalars().all()
        # Load users in ONE query (see below)
        enriched = await _enrich_with_users(db, txns)
        return TransactionListResponse(
            transactions=enriched,
            total=total,
            page=1,
            size=total,
            pages=1,
        )

    # --------------------------------------------------------------
    # Normal pagination
    # --------------------------------------------------------------
    stmt = stmt.order_by(desc(Transaction.created_at))
    stmt = stmt.offset((page - 1) * size).limit(size)

    result = await db.execute(stmt)
    txns = result.scalars().all()

    # Enrich with user objects
    enriched = await _enrich_with_users(db, txns)

    return TransactionListResponse(
        transactions=enriched,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


# ----------------------------------------------------------------------
# Helper – load all needed Users in ONE query and attach them
# ----------------------------------------------------------------------
async def _enrich_with_users(db: AsyncSession, transactions: List[Transaction]) -> List[TransactionOut]:
    """
    Given a list of Transaction objects, fetch the related Users (if any)
    in a single SELECT and attach them to a Pydantic model.
    """
    # Collect all user_ids that are not None
    user_ids = {t.user_id for t in transactions if t.user_id is not None}
    if not user_ids:
        # No users to load → just convert
        return [TransactionOut.model_validate(t) for t in transactions]

    # ONE query → dict[user_id → User]
    user_result = await db.execute(
        select(User).where(User.user_id.in_(user_ids))
    )
    user_map = {u.user_id: u for u in user_result.scalars().all()}

    # Build enriched output models
    out = []
    for txn in transactions:
        user = user_map.get(txn.user_id) if txn.user_id else None
        data = TransactionOut.model_validate(txn).model_dump()
        data["user"] = UserResponse.model_validate(user) if user else None
        out.append(TransactionOut(**data))
    return out