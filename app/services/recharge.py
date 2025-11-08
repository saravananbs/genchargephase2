from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from ..schemas.recharge import CurrentPlanFilterParams
from ..schemas.users import UserResponse
from ..models.users import User
from ..models.current_active_plans import CurrentActivePlan
from ..models.transactions import Transaction
from ..services.notification import create_custom_notification

from ..crud.recharge import (
    get_user_by_phone,
    get_plan_by_id,
    get_offer_by_id,
    create_active_plan,
    create_transaction,
    activate_queued_plan,
    list_active_plans,
    list_transactions,
)
from ..schemas.recharge import (
    RechargeRequest,
    WalletTopupRequest,
    TransactionOut,
    CurrentActivePlanOut,
    CurrentPlanListResponse,
    TransactionListResponse,
    TransactionFilterParams
)
from ..models.transactions import (
    TransactionCategory,
    TransactionType,
    TransactionSource,
    TransactionStatus,
    ServiceType,
    PaymentMethod,
)
from ..models.current_active_plans import CurrentPlanStatus
from ..crud.referrals import claim_referral_if_eligible

# ---------- Criteria / Reward helpers ----------
def evaluate_criteria(criteria: Optional[dict], context: dict) -> bool:
    if not criteria or "conditions" not in criteria:
        return True

    cond = criteria["conditions"]
    now = datetime.now()

    if cond.get("valid_from"):
        if datetime.fromisoformat(cond["valid_from"].replace("Z", "+00:00")) > now:
            return False
    if cond.get("valid_to"):
        if datetime.fromisoformat(cond["valid_to"].replace("Z", "+00:00")) < now:
            return False

    if "min_amount" in cond and context.get("amount", 0) < cond["min_amount"]:
        return False
    if "user_type" in cond and context.get("user_type") not in cond["user_type"]:
        return False
    if cond.get("is_new_user") and not context.get("is_new_user"):
        return False
    if "applicable_sources" in cond and context.get("source") not in cond["applicable_sources"]:
        return False
    if "valid_plan_groups" in cond:
        pg = context.get("plan_group_name")
        if not pg or pg not in cond["valid_plan_groups"]:
            return False
    return True


def calculate_reward(offer_criteria: dict, plan_amount: Decimal) -> Tuple[Decimal, Decimal]:
    discount = cashback = Decimal("0")
    rewards = offer_criteria.get("rewards", {})

    if rewards.get("discount_type") == "flat":
        discount = Decimal(str(rewards["discount_value"]))
    if rewards.get("cashback_type") == "flat":
        cashback = Decimal(str(rewards["cashback_value"]))

    discount = min(discount, plan_amount)
    return discount, cashback


def _decide_plan_status(has_active: bool, force_queue: bool, force_activate: bool) -> CurrentPlanStatus:
    if force_queue:
        return CurrentPlanStatus.queued
    if not has_active or force_activate:
        return CurrentPlanStatus.active
    return CurrentPlanStatus.queued


# ---------- Public service functions ----------
async def subscribe_plan(
    db: AsyncSession,
    request: RechargeRequest,
    current_user: User,
    mongo_db: AsyncIOMotorDatabase
) -> TransactionOut:
    # Resolve target user
    target_user = await get_user_by_phone(db, request.phone_number)

    # Load plan & optional offer
    plan = await get_plan_by_id(db, request.plan_id)
    offer = None
    if request.offer_id:
        offer = await get_offer_by_id(db, request.offer_id)

    # Build context
    plan_amount = plan.price
    if plan_amount < 0:
        raise ValueError("Plan price not defined")

    context = {
        "amount": plan_amount,
        "user_type": target_user.user_type.value,
        "is_new_user": False,
        "source": request.source.value,
        "plan_group_name": plan.group.group_name if plan.group else None,
    }

    # Validate criteria
    if not evaluate_criteria(plan.criteria, context):
        raise ValueError("User does not meet plan criteria")
    if offer and not evaluate_criteria(offer.criteria, context):
        raise ValueError("Offer criteria not satisfied")

    discount, cashback = calculate_reward(offer.criteria, plan_amount) if offer else (Decimal("0"), Decimal("0"))
    total_deduct = plan_amount - discount

    # Wallet payment check
    if request.payment_method == PaymentMethod.Wallet:
        if current_user.user_id == target_user.user_id and current_user.wallet_balance < total_deduct:
            raise ValueError("Insufficient wallet balance")
        current_user.wallet_balance -= total_deduct

    # Activate any queued plan first
    await activate_queued_plan(db, target_user.user_id, request.phone_number)

    # Decide activation mode
    res = await db.execute(
            select(CurrentActivePlan).where(
                CurrentActivePlan.user_id == target_user.user_id,
                CurrentActivePlan.phone_number == request.phone_number,
                CurrentActivePlan.status == CurrentPlanStatus.active,
            )
        )
    res = res.scalars().first()
    has_active = bool(res)
    force_queue = request.activation_mode == "queue"
    force_activate = request.activation_mode == "activate"
    plan_status = _decide_plan_status(has_active, force_queue, force_activate)

    # Create active plan entry
    valid_from = datetime.now()
    valid_to = valid_from + timedelta(days=plan.validity or 30)
    await create_active_plan(
        db,
        user_id=target_user.user_id,
        plan_id=plan.plan_id,
        phone_number=request.phone_number,
        valid_from=valid_from,
        valid_to=valid_to,
        status=plan_status,
    )

    # Main transaction
    txn = await create_transaction(
        db,
        user_id=current_user.user_id,
        category=TransactionCategory.service,
        txn_type=TransactionType.debit,
        amount=plan_amount,
        service_type=ServiceType.prepaid if plan.plan_type == "prepaid" else ServiceType.postpaid,
        plan_id=plan.plan_id,
        offer_id=offer.offer_id if offer else None,
        from_phone_number=current_user.phone_number,
        to_phone_number=request.phone_number,
        source=request.source,
        status=TransactionStatus.success,
        payment_method=request.payment_method,
        payment_transaction_id=f"PYMT_{datetime.now().timestamp()}",
        created_at=datetime.now(),
    )

    # Cashback transaction
    if cashback > 0:
        await create_transaction(
            db,
            user_id=target_user.user_id,
            category=TransactionCategory.wallet,
            txn_type=TransactionType.credit,
            amount=cashback,
            source=TransactionSource.offer_cashback,
            status=TransactionStatus.success,
            created_at=datetime.now(),
        )
        target_user.wallet_balance += cashback

    
    stmt = select(User).where(User.referral_code == current_user.referee_code)
    result = await db.execute(stmt)
    referrer = result.scalars().first()
    existing = await claim_referral_if_eligible(db=db, referrer=referrer, referred=current_user)   
    await db.commit()
    await db.refresh(txn)

    notify_user = await get_user_by_phone(db, request.phone_number)
    #create a notification
    await create_custom_notification(
        db=mongo_db, 
        description= f"Recharge for Rs.{plan_amount} is done for mobile number {request.phone_number} on {datetime.now()} plan details - plan name: {plan.plan_name}, plan type: {plan.plan_type}, validity: {plan.validity} price: {plan.price}", 
        recipient_type="user", recipient_id=notify_user.user_id, notif_type="message"
    )
    await create_custom_notification(
        db=mongo_db, 
        description= f"Recharge for Rs.{plan_amount} is done for mobile number {request.phone_number} on {datetime.now()}. plan details - plan name: {plan.plan_name}, plan type: {plan.plan_type}, validity: {plan.validity} price: {plan.price}", 
        recipient_type="user", recipient_id=notify_user.user_id, notif_type="in-app"
    )

    #bill remainder
    await create_custom_notification(
        db=mongo_db, description= f"Bill is on due for mobile number {request.phone_number}", recipient_type="user", 
        recipient_id=notify_user.user_id, notif_type="message", scheduled_at=(datetime.now() + timedelta(days=(plan.validity-1)))
    )
    await create_custom_notification(
        db=mongo_db, description= f"Bill is on due for mobile number {request.phone_number}", recipient_type="user", 
        recipient_id=notify_user.user_id, notif_type="in-app", scheduled_at=(datetime.now() + timedelta(days=(plan.validity-1)))
    )


    return TransactionOut.model_validate(txn)


async def wallet_topup(
    db: AsyncSession,
    mongo_db: AsyncIOMotorDatabase,
    request: WalletTopupRequest,
    current_user: User,
) -> TransactionOut:
    target_phone = request.phone_number or current_user.phone_number
    target_user = await get_user_by_phone(db, target_phone)

    if request.payment_method == PaymentMethod.Wallet and current_user.wallet_balance < request.amount:
        raise ValueError("Insufficient wallet balance")

    if request.payment_method == PaymentMethod.Wallet:
        current_user.wallet_balance -= request.amount

    target_user.wallet_balance += request.amount

    txn = await create_transaction(
        db,
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
        created_at=datetime.now(),
    )
    notify_user = await get_user_by_phone(db, request.phone_number)
    #create a notification
    await create_custom_notification(
        db=mongo_db, 
        description= f"Recharge for Rs.{request.amount} is done for mobile number {request.phone_number} on {datetime.now()}.", 
        recipient_type="user", recipient_id=notify_user.user_id, notif_type="message"
    )
    await create_custom_notification(
        db=mongo_db, 
        description= f"Recharge for Rs.{request.amount} is done for mobile number {request.phone_number} on {datetime.now()}.", 
        recipient_type="user", recipient_id=notify_user.user_id, notif_type="in-app"
    )
    await db.commit()
    await db.refresh(txn)
    return TransactionOut.model_validate(txn)


async def get_my_active_plans(
    db: AsyncSession,
    f: CurrentPlanFilterParams,
) -> CurrentPlanListResponse:
    plans, total = await list_active_plans(db, f)
    return CurrentPlanListResponse(
        plans=[CurrentActivePlanOut.model_validate(p) for p in plans],
        total=total,
        page=f.page,
        size=f.size,
        pages=(total + f.size - 1) // f.size,
    )

async def get_my_transactions(
    db: AsyncSession,
    f: TransactionFilterParams,
) -> TransactionListResponse:
    txns, total = await list_transactions(db, f)

    enriched = await _enrich_transactions_with_user(db, txns)

    # pagination meta
    if f.size == 0:
        page, size, pages = 1, total, 1
    else:
        page, size = f.page, f.size
        pages = (total + size - 1) // size

    return TransactionListResponse(
        transactions=enriched,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


# ---------- Admin services ----------
async def admin_list_active_plans(
    db: AsyncSession,
    f: CurrentPlanFilterParams,
) -> CurrentPlanListResponse:
    plans, total = await list_active_plans(db, f)
    return CurrentPlanListResponse(
        plans=[CurrentActivePlanOut.model_validate(p) for p in plans],
        total=total,
        page=f.page,
        size=f.size,
        pages=(total + f.size - 1) // f.size,
    )


async def admin_list_transactions(
    db: AsyncSession,
    f: TransactionFilterParams,
) -> TransactionListResponse:
    txns, total = await list_transactions(db, f)

    enriched = await _enrich_transactions_with_user(db, txns)

    # pagination meta
    if f.size == 0:
        page, size, pages = 1, total, 1
    else:
        page, size = f.page, f.size
        pages = (total + size - 1) // size

    return TransactionListResponse(
        transactions=enriched,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


# ---------- Helper to attach User to TransactionOut ----------
async def _enrich_transactions_with_user(
    db: AsyncSession, txns: List[Transaction]
) -> List[TransactionOut]:
    user_ids = {t.user_id for t in txns if t.user_id}
    if not user_ids:
        return [TransactionOut.model_validate(t) for t in txns]

    users = await db.execute(select(User).where(User.user_id.in_(user_ids)))
    user_map = {u.user_id: u for u in users.scalars().all()}

    out = []
    for t in txns:
        data = TransactionOut.model_validate(t).model_dump()
        if t.user_id:
            data["user"] = UserResponse.model_validate(user_map[t.user_id])
        out.append(TransactionOut(**data))
    return out