from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo

from ..models.transactions import Transaction
from ..models.current_active_plans import CurrentActivePlan
from ..models.users import User

TZ = ZoneInfo("Asia/Kolkata")

def to_aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(TZ)

def make_naive(dt: datetime):
    if dt.tzinfo:
        return dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    return dt

# ---- Helper period generator ----
def build_periods():
    now = datetime.now(TZ)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        "last_week": (today - timedelta(days=7), now),
        "last_30_days": (today - timedelta(days=30), now),
        "last_3_months": (today - timedelta(days=90), now),
        "last_6_months": (today - timedelta(days=183), now),
        "last_year": (today - timedelta(days=365), now)
    }

# ---- User profile ----
async def get_user_profile(db: AsyncSession, user_id: int) -> Optional[Dict]:
    q = select(User).where(User.user_id == user_id)
    res = await db.execute(q)
    user = res.scalar_one_or_none()
    if not user:
        return None
    created_at = to_aware(user.created_at)
    days = (datetime.now(TZ) - created_at).days if created_at else 0
    return {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "user_type": user.user_type.value if user.user_type else None,
        "status": user.status.value if user.status else None,
        "wallet_balance": float(user.wallet_balance or 0),
        "created_at": created_at,
        "account_age_days": days
    }

# ---- Transaction insights ----
async def transaction_summary(db: AsyncSession, user_id: int) -> Dict:
    q = select(
        func.count().label("total"),
        func.sum(case((Transaction.txn_type == "debit", 1), else_=0)).label("debit_count"),
        func.sum(case((Transaction.txn_type == "credit", 1), else_=0)).label("credit_count"),
        func.sum(case((Transaction.status == "success", 1), else_=0)).label("success"),
        func.sum(case((Transaction.status == "failed", 1), else_=0)).label("failed"),
        func.sum(case((Transaction.status == "pending", 1), else_=0)).label("pending"),
        func.sum(case((Transaction.txn_type == "debit", Transaction.amount), else_=0)).label("spent"),
        func.sum(case((Transaction.txn_type == "credit", Transaction.amount), else_=0)).label("credited"),
    ).where(Transaction.user_id == user_id)
    res = await db.execute(q)
    r = res.first()
    return {
        "success": int(r[3] or 0),
        "failed": int(r[4] or 0),
        "pending": int(r[5] or 0),
        "credit_count": int(r[2] or 0),
        "debit_count": int(r[1] or 0),
        "total_amount_spent": float(r[6] or 0),
        "total_amount_credited": float(r[7] or 0)
    }

# ---- Spending by period ----
async def spending_by_period(db: AsyncSession, user_id: int) -> List[Dict]:
    periods = build_periods()
    out = []
    for label, (s, e) in periods.items():
        q = select(
            func.count(),
            func.coalesce(func.sum(Transaction.amount), 0)
        ).where(
            Transaction.user_id == user_id,
            Transaction.txn_type == "debit",
            Transaction.status == "success",
            Transaction.created_at >= make_naive(s),
            Transaction.created_at <= make_naive(e)
        )
        res = await db.execute(q)
        c, amt = res.first()
        out.append({"label": label, "total_spent": float(amt or 0), "txn_count": int(c or 0)})
    return out

# ---- Recharge numbers ----
async def recharge_numbers(db: AsyncSession, user_id: int) -> List[Dict]:
    q = select(Transaction.to_phone_number, func.count()).where(
        Transaction.user_id == user_id,
        Transaction.source == "recharge"
    ).group_by(Transaction.to_phone_number).order_by(func.count().desc())
    res = await db.execute(q)
    return [{"phone_number": r[0], "count": int(r[1])} for r in res.all()]

# ---- Top plan ----
async def most_used_plan(db: AsyncSession, user_id: int) -> Optional[Dict]:
    q = (
        select(Transaction.plan_id, func.count())
        .where(Transaction.user_id == user_id, Transaction.plan_id.isnot(None))
        .group_by(Transaction.plan_id)
        .order_by(func.count().desc())
        .limit(1)
    )
    res = await db.execute(q)
    r = res.first()
    if not r:
        return None
    return {"plan_id": r[0], "usage_count": int(r[1])}

# ---- Top offer ----
async def most_used_offer(db: AsyncSession, user_id: int) -> Optional[Dict]:
    q = (
        select(Transaction.offer_id, func.count())
        .where(Transaction.user_id == user_id, Transaction.offer_id.isnot(None))
        .group_by(Transaction.offer_id)
        .order_by(func.count().desc())
        .limit(1)
    )
    res = await db.execute(q)
    r = res.first()
    if not r:
        return None
    return {"offer_id": r[0], "usage_count": int(r[1])}

# ---- Payment methods ----
async def top_payment_methods(db: AsyncSession, user_id: int) -> List[Dict]:
    q = select(Transaction.payment_method, func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id, Transaction.payment_method.isnot(None)
    ).group_by(Transaction.payment_method).order_by(func.sum(Transaction.amount).desc())
    res = await db.execute(q)
    return [{"payment_method": r[0].value if hasattr(r[0], "value") else r[0], "total_amount": float(r[1])} for r in res.all()]

# ---- Top sources ----
async def top_sources(db: AsyncSession, user_id: int) -> List[Dict]:
    q = select(Transaction.source, func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id
    ).group_by(Transaction.source).order_by(func.sum(Transaction.amount).desc())
    res = await db.execute(q)
    return [{"source": r[0].value if hasattr(r[0], "value") else r[0], "total_amount": float(r[1])} for r in res.all()]

# ---- Timeline ----
async def user_transaction_timeline(db: AsyncSession, user_id: int) -> Dict:
    q = select(func.min(Transaction.created_at), func.max(Transaction.created_at)).where(Transaction.user_id == user_id)
    res = await db.execute(q)
    first, last = res.first()
    return {"first": first, "last": last}
