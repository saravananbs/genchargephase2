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
    """
    Get admin analytics dashboard.
    
    Comprehensive analytics on admin team including active admins, role
    distribution, permission usage, and admin activity trends.
    
    Security:
        - Requires valid JWT access token
        - Scope: Admins:read
        - Restricted to super-admin
    
    Returns:
        AdminsReport:
            - total_admins (int): Total admin count
            - active_admins (int): Currently active admins
            - by_role (dict): Admins grouped by role
            - permission_distribution (dict): Permission usage stats
            - activity_trends (list): Historical trends
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Admins:read scope
        HTTPException(500): Analytics computation failed
    """
    try:
        return await build_admins_report(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/backup", response_model=BackupsReport)
async def get_backups_report(
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Backup:read"])
):
    """
    Get backup analytics dashboard.
    
    Shows backup health metrics including backup frequency, success rates,
    storage usage, and disaster recovery readiness.
    
    Security:
        - Requires valid JWT access token
        - Scope: Backup:read
        - Restricted to admin/operations
    
    Returns:
        BackupsReport:
            - total_backups (int): Total backups created
            - successful (int): Successful backups
            - failed (int): Failed backup attempts
            - total_storage_mb (float): Total backup storage used
            - last_backup (datetime): Most recent backup timestamp
            - success_rate (float): Percentage of successful backups
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Backup:read scope
        HTTPException(500): Analytics computation failed
    """
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
    """
    Get active plan subscriptions analytics.
    
    Real-time metrics on currently active plan subscriptions including distribution
    by plan type, expiration timeline, and revenue tracking.
    
    Security:
        - Requires valid JWT access token
        - Scope: Plans:read
        - Restricted to admin/business team
    
    Returns:
        CurrentActivePlansReport:
            - total_active (int): Total active subscriptions
            - by_plan_type (dict): Distribution by plan type
            - by_validity_days (dict): Grouping by remaining validity
            - expiring_soon (int): Plans expiring within 7 days
            - expiring_today (int): Plans expiring today
            - revenue_potential (float): Expected revenue from active plans
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Plans:read scope
        HTTPException(500): Analytics computation failed
    """
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
    """
    Get promotional offers analytics dashboard.
    
    Analyzes offer program effectiveness including redemption rates, discount
    impact on revenue, and offer performance rankings.
    
    Security:
        - Requires valid JWT access token
        - Scope: Offers:read
        - Restricted to admin/marketing team
    
    Returns:
        OffersReport:
            - total_offers (int): Total offers in system
            - active_offers (int): Currently active offers
            - total_redemptions (int): Total offer usages
            - discount_given (float): Total discount distributed
            - top_offers (list): Best performing offers
            - roi_metrics (dict): Return on investment analysis
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Offers:read scope
        HTTPException(500): Analytics computation failed
    """
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
    """
    Get recharge plan analytics dashboard.
    
    Comprehensive plan metrics including adoption rates, revenue contribution,
    popularity trends, and user preferences across plan types.
    
    Security:
        - Requires valid JWT access token
        - Scope: Plans:read
        - Restricted to admin/product team
    
    Returns:
        PlansReport:
            - total_plans (int): Total plans available
            - by_type (dict): Distribution by plan type (voice, data, etc.)
            - total_subscriptions (int): Lifetime plan subscriptions
            - active_subscriptions (int): Currently active
            - revenue_by_plan (dict): Revenue contribution per plan
            - growth_trends (list): Historical adoption trends
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Plans:read scope
        HTTPException(500): Analytics computation failed
    """
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
    """
    Get referral program analytics dashboard.
    
    Analyzes referral program performance including conversion rates, user
    acquisition cost through referrals, and reward distribution metrics.
    
    Security:
        - Requires valid JWT access token
        - Scope: Referral:read
        - Restricted to admin/growth team
    
    Returns:
        ReferralsReport:
            - total_referrals (int): Total referral links shared
            - successful_referrals (int): Referrals resulting in conversion
            - conversion_rate (float): Percentage of successful referrals
            - total_rewards (float): Total rewards distributed
            - active_referrers (int): Users actively referring others
            - top_referrers (list): Leaderboard of best referrers
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Referral:read scope
        HTTPException(500): Analytics computation failed
    """
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
    """
    Get financial transaction analytics dashboard.
    
    Core financial metrics including total revenue, payment methods distribution,
    transaction trends, refund rates, and payment failures analysis.
    
    Security:
        - Requires valid JWT access token
        - Scope: Recharge:read
        - Restricted to admin/finance team
    
    Returns:
        TransactionsReport:
            - total_transactions (int): Lifetime transaction count
            - total_revenue (float): Total money received
            - successful_transactions (int): Successful payments
            - failed_transactions (int): Failed payment attempts
            - by_payment_method (dict): Distribution across payment gateways
            - refunds_total (float): Total refunded amount
            - average_transaction_value (float): Mean transaction amount
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Recharge:read scope
        HTTPException(500): Analytics computation failed
    """
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
    """
    Get archived/deactivated users analytics.
    
    Churn analysis showing deactivated accounts, reasons for leaving, and
    trends in user retention and abandonment.
    
    Security:
        - Requires valid JWT access token
        - Scope: Users:read
        - Restricted to admin/analytics team
    
    Returns:
        UsersArchiveReport:
            - total_archived (int): Total deactivated accounts
            - archived_this_month (int): Deactivations this month
            - archived_this_year (int): Deactivations this year
            - churn_rate (float): Monthly churn percentage
            - by_reason (dict): Deactivation reasons breakdown
            - monthly_trends (list): Deactivation trends over time
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Users:read scope
        HTTPException(500): Analytics computation failed
    """
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
    Get comprehensive user base analytics dashboard.
    
    Full user analytics including total users, growth trends, demographics,
    account types distribution, and engagement metrics. Core business intelligence.
    
    Security:
        - Requires valid JWT access token
        - Scope: Users:read
        - Restricted to admin/business team
    
    Returns:
        UsersReport:
            - total_users (int): Total user accounts
            - active_users (int): Currently active users
            - inactive_users (int): Inactive accounts
            - by_type (dict): Prepaid vs postpaid breakdown
            - by_status (dict): Account status distribution
            - growth_rate (float): Monthly growth percentage
            - monthly_trends (list): User growth historical data
            - engagement_score (float): Overall user engagement metric
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Users:read scope
        HTTPException(500): Analytics computation failed
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
    authorized = Security(require_scopes, scopes=["User"])

):
    """
    Get personal user insights and analytics.
    
    Personalized dashboard showing current user's own account metrics including
    spending patterns, plan usage, offer usage, referral earnings, and activity.
    
    Security:
        - Requires valid JWT access token
        - Scope: User
        - Users can only view their own insights
    
    Returns:
        UserInsightReport:
            - user_id (int): Current user's ID
            - account_age_days (int): Days since account creation
            - total_spent (float): Lifetime spending
            - active_plans (int): Currently active subscriptions
            - total_recharges (int): Lifetime recharge count
            - offers_used (int): Offers/discounts claimed
            - referral_earnings (float): Rewards from referrals
            - activity_score (float): User engagement score
            - last_active (datetime): Last account activity
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing User scope
        HTTPException(404): User account not found
        HTTPException(500): Analytics computation failed
    
    Example:
        Request:
            GET /analytics/me/users
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            {
                "user_id": 42,
                "account_age_days": 365,
                "total_spent": 2500.50,
                "active_plans": 2,
                "total_recharges": 35,
                "offers_used": 8,
                "referral_earnings": 125.00,
                "activity_score": 8.5,
                "last_active": "2024-01-20T10:30:00Z"
            }
    """
    try:
        report = await build_user_insight_report(db, current_user.user_id)
        return report
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
 