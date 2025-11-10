# app/crud/plan.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.plans import Plan  # your Plan model

async def get_plan_by_id(db: AsyncSession, plan_id: int) -> Plan | None:
    """
    Retrieve a Plan by its primary key.

    Args:
        db (AsyncSession): Async database session.
        plan_id (int): Primary key of the plan to retrieve.

    Returns:
        Optional[Plan]: The Plan instance if found, otherwise None.
    """
    stmt = select(Plan).where(Plan.plan_id == plan_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()