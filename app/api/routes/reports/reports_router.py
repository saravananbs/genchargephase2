from fastapi import APIRouter, Depends, Security
from fastapi.encoders import jsonable_encoder
from ....models.admins import Admin
from ....models.users import User
from dataclasses import asdict
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from ....schemas.reports import (
    AdminReportFilter, AutoPayReportFilter, BackupReportFilter, CurrentActivePlansFilter,
    OfferReportFilter, PlanReportFilter, ReferralReportFilter, RolePermissionReportFilter,
    SessionsReportFilter, TransactionsReportFilter, UsersArchiveFilter, UsersReportFilter, UserTransactionsReportFilter
)
from ....services.reports import (
    generate_admin_report, generate_autopay_report, generate_backup_report, generate_current_active_plans_report,
    generate_offers_report, generate_plans_report, generate_referral_report, generate_role_permission_report,
    generate_sessions_report, generate_transactions_report, generate_users_archive_report, generate_users_report
)
from ....core.database import get_db


router = APIRouter()


@router.get("/admins-report")
async def admin_report(
    filters: AdminReportFilter = Depends(), 
    session=Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Admins:read"])
):
    """
    Generate admin management report.
    
    Produces a comprehensive report of all system admins with detailed information
    including roles, permissions, activity levels, and access history. Can be
    viewed as JSON data or exported to CSV/Excel/PDF format.
    
    Security:
        - Requires valid JWT access token
        - Scope: Admins:read
        - Restricted to super-admin
    
    Query Parameters (AdminReportFilter):
        - role_id (int, optional): Filter by admin role
        - limit (int, optional): Records per page (0 = all)
        - offset (int, optional): Pagination offset
        - export_format (str, optional): Export format (json, csv, excel, pdf)
        - order_by (str, optional): Sort field
        - order_dir (str, optional): Sort direction (asc/desc)
    
    Returns:
        Union[JSONResponse, StreamingResponse]:
            - JSON: Array of admin objects with full details
            - File: CSV/Excel/PDF download with formatted report
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Admins:read scope
        HTTPException(400): Invalid filter parameters
    
    Example:
        Request:
            GET /reports/admins-report?limit=50&export_format=csv
            Headers: Authorization: Bearer <jwt_token>
        
        Response:
            - CSV file download or JSON array
    """
    result = await generate_admin_report(session, filters)

    # If it's a simple data response
    if isinstance(result, list):
        encoded = jsonable_encoder(result)
        return JSONResponse(content=encoded)

    # If it’s a file download
    buffer, content_type, filename = result
    return StreamingResponse(buffer, media_type=content_type, headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })


@router.get("/autopay-report")
async def autopay_report(
    filters: AutoPayReportFilter = Depends(),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Autopay:read"])

):
    """
    Generate autopay program report.
    
    Generates a detailed report of all autopay rules including status, frequency,
    success/failure rates, and revenue impact. Shows recurring recharge patterns
    and program adoption metrics. Supports JSON view and file export.
    
    Security:
        - Requires valid JWT access token
        - Scope: Autopay:read
        - Restricted to admin/analytics
    
    Query Parameters (AutoPayReportFilter):
        - status (str, optional): Filter by autopay status (active, paused, completed)
        - limit (int, optional): Records per page (0 = all)
        - offset (int, optional): Pagination offset
        - export_format (str, optional): Output format (json, csv, excel, pdf)
    
    Returns:
        Union[JSONResponse, StreamingResponse]:
            - JSON: Autopay statistics and detailed list
            - File: Formatted report download
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Autopay:read scope
    
    Example:
        Request:
            GET /reports/autopay-report?status=active&export_format=pdf
            Headers: Authorization: Bearer <jwt_token>
    """
    result = await generate_autopay_report(session, filters)

    # If JSON/list
    if isinstance(result, list) or isinstance(result, dict):
        # Ensure JSON serializable
        return JSONResponse(content=jsonable_encoder(result))

    # Otherwise it's a file (buffer, content_type, filename)
    buffer, content_type, filename = result
    return StreamingResponse(buffer, media_type=content_type, headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })


@router.get("/backup-report")
async def backup_report(
    filters: BackupReportFilter = Depends(),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Backup:read"])

):
    """
    Generate database backup report.
    
    Shows backup history, sizes, success/failure rates, and restore operations.
    Useful for data retention compliance and disaster recovery planning.
    
    Security:
        - Requires valid JWT access token
        - Scope: Backup:read
        - Restricted to admin/operations
    
    Query Parameters (BackupReportFilter):
        - status (str, optional): Filter by backup status
        - export_format (str, optional): Format (json, csv, excel, pdf)
        - limit (int, optional): Records per page (0 = all)
        - offset (int, optional): Pagination offset
    
    Returns:
        Union[JSONResponse, StreamingResponse]
    """
    result = await generate_backup_report(session, filters)

    # JSON response
    if isinstance(result, list):
        return JSONResponse(content=jsonable_encoder(result))

    # File response
    buffer, content_type, filename = result
    return StreamingResponse(
        buffer,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/current-active-plans-report")
async def current_active_plans_report(
    filters: CurrentActivePlansFilter = Depends(),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Recharge:read"])

):
    """
    Generate active plan subscriptions report.
    
    Shows all currently active user plan subscriptions with expiry dates,
    renewal dates, and subscription status. Key metric for revenue tracking.
    
    Security:
        - Requires valid JWT access token
        - Scope: Recharge:read
        - Restricted to admin/business analytics
    
    Query Parameters (CurrentActivePlansFilter):
        - user_type (str, optional): Filter by prepaid/postpaid
        - export_format (str, optional): Output format
        - limit (int, optional): Records per page (0 = all)
    
    Returns:
        Union[JSONResponse, StreamingResponse]
    """
    result = await generate_current_active_plans_report(session, filters)

    # If JSON/list
    if isinstance(result, list) or isinstance(result, dict):
        return JSONResponse(content=jsonable_encoder(result))

    # File response (buffer, content_type, filename)
    buffer, content_type, filename = result
    return StreamingResponse(buffer, media_type=content_type, headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })


@router.get("/offers-report")
async def offers_report(
    filters: OfferReportFilter = Depends(),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Offers:read"])

):
    """
    Generate promotional offers report.
    
    Analyzes offer program effectiveness including redemption rates, discount
    impact, and ROI. Shows which offers drive the most user engagement.
    
    Security:
        - Requires valid JWT access token
        - Scope: Offers:read
        - Restricted to admin/marketing
    
    Query Parameters (OfferReportFilter):
        - status (str, optional): Filter by offer status
        - export_format (str, optional): Format (json, csv, excel, pdf)
        - limit (int, optional): Records per page (0 = all, otherwise both limit & offset required)
    
    Returns:
        Union[JSONResponse, StreamingResponse]: Report data or file download
    """
    result = await generate_offers_report(session, filters)

    # JSON
    if isinstance(result, list) or isinstance(result, dict):
        return JSONResponse(content=jsonable_encoder(result))

    # file response
    buffer, content_type, filename = result
    return StreamingResponse(buffer, media_type=content_type, headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })


@router.get("/plans-report")
async def plans_report(
    filters: PlanReportFilter = Depends(),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Plans:read"])
):
    """
    Generate recharge plan report.
    
    Comprehensive analysis of all plans including adoption rates, popularity,
    revenue contribution, and subscription trends over time.
    
    Security:
        - Requires valid JWT access token
        - Scope: Plans:read
        - Restricted to admin/product team
    
    Query Parameters (PlanReportFilter):
        - plan_type (str, optional): Filter by type (voice, data, voice_data, ott)
        - export_format (str, optional): Output format
        - limit (int, optional): Records per page (0 = all)
    
    Returns:
        Union[JSONResponse, StreamingResponse]
    """
    result = await generate_plans_report(session, filters)

    if isinstance(result, list) or isinstance(result, dict):
        return JSONResponse(content=jsonable_encoder(result))

    buffer, content_type, filename = result
    return StreamingResponse(buffer, media_type=content_type, headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })


@router.get("/referral-report")
async def referral_report(
    filters: ReferralReportFilter = Depends(),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Referral:read"])

):
    """
    Generate referral program report.
    
    Analyzes referral program performance including total referrals, conversion
    rates, reward distribution, and user acquisition cost through referrals.
    
    Security:
        - Requires valid JWT access token
        - Scope: Referral:read
        - Restricted to admin/growth team
    
    Query Parameters (ReferralReportFilter):
        - status (str, optional): Filter by reward status
        - export_format (str, optional): Format (json, csv, excel, pdf)
        - limit (int, optional): Records per page (pagination only when limit>0 AND offset>0)
    
    Returns:
        Union[JSONResponse, StreamingResponse]
    """
    result = await generate_referral_report(session, filters)

    if isinstance(result, list) or isinstance(result, dict):
        return JSONResponse(content=jsonable_encoder(result))

    buffer, content_type, filename = result
    return StreamingResponse(buffer, media_type=content_type, headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })


@router.get("/role-permission-report")
async def role_permissions_report(
    filters: RolePermissionReportFilter = Depends(),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Admins:read"])
):
    """
    Generate role and permission matrix report.
    
    Shows role hierarchy and their associated permissions. Used for security
    audits and access control verification. Identifies permission gaps or
    excessive privileges.
    
    Security:
        - Requires valid JWT access token
        - Scope: Admins:read
        - Restricted to super-admin
    
    Query Parameters (RolePermissionReportFilter):
        - role_name (str, optional): Filter by specific role
        - export_format (str, optional): Output format
        - limit (int, optional): Records per page (pagination only when limit>0 AND offset>0)
    
    Returns:
        Union[JSONResponse, StreamingResponse]
    """
    result = await generate_role_permission_report(session, filters)

    if isinstance(result, list) or isinstance(result, dict):
        return JSONResponse(content=jsonable_encoder(result))

    buffer, content_type, filename = result
    return StreamingResponse(
        buffer,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/sessions-report")
async def sessions_report(
    filters: SessionsReportFilter = Depends(),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Sessions:read"])

):
    """
    Generate user session and login report.
    
    Analyzes user login patterns, session duration, device types, and geographic
    distribution. Useful for understanding user engagement and identifying
    security anomalies.
    
    Security:
        - Requires valid JWT access token
        - Scope: Sessions:read
        - Restricted to admin/security team
    
    Query Parameters (SessionsReportFilter):
        - status (str, optional): Filter by session status
        - export_format (str, optional): Format (json, csv, excel, pdf)
        - limit (int, optional): Records per page (pagination when limit>0 AND offset>0)
    
    Returns:
        Union[JSONResponse, StreamingResponse]
    """
    result = await generate_sessions_report(session, filters)

    # JSON/list
    if isinstance(result, list) or isinstance(result, dict):
        return JSONResponse(content=jsonable_encoder(result))

    # file response
    buffer, content_type, filename = result
    return StreamingResponse(buffer, media_type=content_type, headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })


@router.get("/transactions-report")
async def transactions_report(
    filters: TransactionsReportFilter = Depends(),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Recharge:read"])

):
    """
    Generate transaction and payment report.
    
    Detailed financial report showing all recharge transactions, payments,
    refunds, and revenue. Core business metric for financial tracking and
    reconciliation.
    
    Security:
        - Requires valid JWT access token
        - Scope: Recharge:read
        - Restricted to admin/finance team
    
    Query Parameters (TransactionsReportFilter):
        - status (str, optional): Filter by transaction status
        - amount_min (float, optional): Minimum transaction amount
        - export_format (str, optional): Format (json, csv, excel, pdf)
        - limit (int, optional): Records per page (pagination when limit>0 AND offset>0)
    
    Returns:
        Union[JSONResponse, StreamingResponse]
    """
    result = await generate_transactions_report(session, filters)

    if isinstance(result, list) or isinstance(result, dict):
        return JSONResponse(content=jsonable_encoder(result))

    buffer, content_type, filename = result
    return StreamingResponse(buffer, media_type=content_type, headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })


@router.get("/archived-users-report")
async def users_archive_report(
    filters: UsersArchiveFilter = Depends(),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Users:read"])

):
    """
    Generate archived/deactivated users report.
    
    Shows users who have deactivated or archived their accounts. Useful for
    churn analysis and understanding user retention metrics.
    
    Security:
        - Requires valid JWT access token
        - Scope: Users:read
        - Restricted to admin/analytics
    
    Query Parameters (UsersArchiveFilter):
        - archived_date_from (datetime, optional): Filter by archive date range
        - export_format (str, optional): Format (json, csv, excel, pdf)
        - limit (int, optional): Records per page (all when limit=0)
    
    Returns:
        Union[JSONResponse, StreamingResponse]
    """
    result = await generate_users_archive_report(session, filters)

    # JSON/list
    if isinstance(result, list) or isinstance(result, dict):
        return JSONResponse(content=jsonable_encoder(result))

    # file response
    buffer, content_type, filename = result
    return StreamingResponse(buffer, media_type=content_type, headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })


@router.get("/users-report")
async def users_report(
    filters: UsersReportFilter = Depends(),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Users:read"])

):
    """
    Generate user analytics report.
    
    Comprehensive user base analysis including demographics, registration trends,
    account types, activity levels, and engagement metrics. Key report for
    business intelligence.
    
    Security:
        - Requires valid JWT access token
        - Scope: Users:read
        - Restricted to admin/business analytics
    
    Query Parameters (UsersReportFilter):
        - user_type (str, optional): Filter by prepaid/postpaid
        - status (str, optional): Filter by account status
        - export_format (str, optional): Format (json, csv, excel, pdf)
        - limit (int, optional): Records per page (all when limit=0)
    
    Returns:
        Union[JSONResponse, StreamingResponse]
    """
    result = await generate_users_report(session, filters)

    if isinstance(result, list) or isinstance(result, dict):
        return JSONResponse(content=jsonable_encoder(result))

    buffer, content_type, filename = result
    return StreamingResponse(buffer, media_type=content_type, headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })


@router.get("/me/transactions-report")
async def transactions_report(
    filters: UserTransactionsReportFilter = Depends(),
    session: AsyncSession = Depends(get_db),
    current_user: User =Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"])
):
    """
    Generate personal transaction report (user view).
    
    Shows the current user's own transaction history and payment records.
    Users can download their personal transaction report for accounting or
    reference purposes.
    
    Security:
        - Requires valid JWT access token
        - Scope: User
        - Users can only view their own transactions
    
    Query Parameters (UserTransactionsReportFilter):
        - status (str, optional): Filter by transaction status
        - export_format (str, optional): Format (json, csv, excel, pdf)
        - limit (int, optional): Records per page (all when limit=0)
    
    Returns:
        Union[JSONResponse, StreamingResponse]:
            - JSON: Array of user's transactions
            - File: Personal transaction report download
    
    Example:
        Request:
            GET /reports/me/transactions-report?export_format=pdf
            Headers: Authorization: Bearer <jwt_token>
        
        Response:
            - PDF file download with personal transaction history
    """
    new_filters = TransactionsReportFilter(**asdict(filters))
    new_filters.user_ids = [current_user.user_id]
    result = await generate_transactions_report(session, new_filters)

    if isinstance(result, list) or isinstance(result, dict):
        return JSONResponse(content=jsonable_encoder(result))

    buffer, content_type, filename = result
    return StreamingResponse(buffer, media_type=content_type, headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })

