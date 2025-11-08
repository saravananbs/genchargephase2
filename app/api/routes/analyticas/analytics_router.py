from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ....core.database import get_db
from ....schemas.analytics import UsersReport, AdminsReport
from ....services.analytics import build_users_report, build_admins_report



router = APIRouter()

@router.get("/users", response_model=UsersReport)
async def get_users_report(db: AsyncSession = Depends(get_db)):
    """
    Returns a comprehensive users report with counts, trends, distributions and growth rates.
    """
    try:
        report = await build_users_report(db)
        return report
    except Exception as e:
        # better to log exception in real app
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/admins", response_model=AdminsReport)
async def get_admins_report(db: AsyncSession = Depends(get_db)):
    try:
        return await build_admins_report(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

