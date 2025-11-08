from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.ext.asyncio import AsyncSession
from ....core.database import get_db
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes
from ....models.users import User
from ....models.admins import Admin
from ....schemas.users_admins_analytics import UsersReport, AdminsReport
from ....schemas.backup_analytics import BackupsReport
from ....schemas.current_active_plans_analytics import CurrentActivePlansReport
from ....schemas.offer_analytics import OffersReport
from ....schemas.plan_analytics import PlansReport
from ....schemas.referral_analytics import ReferralsReport
from ....schemas.transaction_analytics import TransactionsReport
from ....schemas.users_archive_analytics import UsersArchiveReport
from ....schemas.user_insights import UserInsightReport
from ....services.users_admin_analytics import build_users_report, build_admins_report
from ....services.backup_analytics import build_backups_report
from ....services.current_active_plans_analytics import build_current_active_plans_report
from ....services.offer_analytics import build_offers_report
from ....services.plan_analytics import build_plans_report
from ....services.referral_analytics import build_referrals_report
from ....services.transactions_analytics import build_transactions_report
from ....services.users_archieve_analytics import build_users_archive_report
from ....services.user_insights import build_user_insight_report

router = APIRouter()

@router.get("/admins", response_model=AdminsReport)
async def get_admins_report(
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Admins:read"])
):
    try:
        return await build_admins_report(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/backup", response_model=BackupsReport)
async def get_backups_report(db: AsyncSession = Depends(get_db)):
    try:
        return await build_backups_report(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/current-active-plans", response_model=CurrentActivePlansReport)
async def get_current_active_plans_report(
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Plans:read"])
):
    try:
        report = await build_current_active_plans_report(db)
        return report
    except Exception as e:
        # in production, log the exception
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/offers", response_model=OffersReport)
async def get_offers_report(
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Offers:read"])
):
    try:
        report = await build_offers_report(db)
        return report
    except Exception as e:
        # log in real app
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/plans", response_model=PlansReport)
async def get_plans_report(
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Plans:read"])
):
    try:
        report = await build_plans_report(db)
        return report
    except Exception as e:
        # log exception in production
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/referrals", response_model=ReferralsReport)
async def get_referrals_report(
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Referral:read"])
):
    try:
        report = await build_referrals_report(db)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions", response_model=TransactionsReport)
async def get_transactions_report(
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Recharge:read"])
):
    try:
        return await build_transactions_report(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/users-archive", response_model=UsersArchiveReport)
async def get_users_archive_report(
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Users:read"])

):
    try:
        return await build_users_archive_report(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
   

@router.get("/users", response_model=UsersReport)
async def get_users_report(
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Users:read"])
):
    """
    Returns a comprehensive users report with counts, trends, distributions and growth rates.
    """
    try:
        report = await build_users_report(db)
        return report
    except Exception as e:
        # better to log exception in real app
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/me/users", response_model=UserInsightReport)
async def get_user_insights(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"], use_cache=False)

):
    try:
        report = await build_user_insight_report(db, current_user.user_id)
        return report
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
 