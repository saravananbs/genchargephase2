from fastapi import APIRouter, Depends, Security
from fastapi.encoders import jsonable_encoder
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from ....schemas.reports import (
    AdminReportFilter, AutoPayReportFilter, BackupReportFilter, CurrentActivePlansFilter,
    OfferReportFilter, PlanReportFilter, ReferralReportFilter, RolePermissionReportFilter,
    SessionsReportFilter, TransactionsReportFilter, UsersArchiveFilter, UsersReportFilter
)
from ....services.reports import (
    generate_admin_report, generate_autopay_report, generate_backup_report, generate_current_active_plans_report,
    generate_offers_report, generate_plans_report, generate_referral_report, generate_role_permission_report,
    generate_sessions_report, generate_transactions_report, generate_users_archive_report, generate_users_report
)
from ....core.database import get_db


router = APIRouter()

@router.post("/admins-report")
async def admin_report(
    filters: AdminReportFilter, session=Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Admins:read"], use_cache=False)

):
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


@router.post("/autopay-report")
async def autopay_report(
    filters: AutoPayReportFilter,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Autopay:read"], use_cache=False)

):
    """
    Request body: AutoPayReportFilter (JSON)
    Returns JSON list or downloadable file (CSV/Excel/PDF).
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


@router.post("/backup-report")
async def backup_report(
    filters: BackupReportFilter,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Backup:read"], use_cache=False)

):
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


@router.post("/current-active-plans-report")
async def current_active_plans_report(
    filters: CurrentActivePlansFilter,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Recharge:read"], use_cache=False)

):
    result = await generate_current_active_plans_report(session, filters)

    # If JSON/list
    if isinstance(result, list) or isinstance(result, dict):
        return JSONResponse(content=jsonable_encoder(result))

    # File response (buffer, content_type, filename)
    buffer, content_type, filename = result
    return StreamingResponse(buffer, media_type=content_type, headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })


@router.post("/offers-report")
async def offers_report(
    filters: OfferReportFilter,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Offers:read"], use_cache=False)

):
    """
    Request body: OfferReportFilter
    Returns: JSON list or downloadable CSV/Excel/PDF
    Pagination will be skipped if either limit==0 or offset==0 (per your requirement).
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


@router.post("/plans-report")
async def plans_report(
    filters: PlanReportFilter, 
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Plans:read"], use_cache=False)
):
    """
    Request body: PlanReportFilter
    Returns JSON list or downloadable CSV/Excel/PDF.
    Pagination will be skipped if either limit==0 or offset==0.
    """
    result = await generate_plans_report(session, filters)

    if isinstance(result, list) or isinstance(result, dict):
        return JSONResponse(content=jsonable_encoder(result))

    buffer, content_type, filename = result
    return StreamingResponse(buffer, media_type=content_type, headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })


@router.post("/referral-report")
async def referral_report(
    filters: ReferralReportFilter,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Referral:read"], use_cache=False)

):
    """
    Request body: ReferralReportFilter
    Returns JSON list or a downloadable CSV/Excel/PDF file.
    Pagination is applied only when both limit>0 AND offset>0; otherwise pagination is skipped.
    """
    result = await generate_referral_report(session, filters)

    if isinstance(result, list) or isinstance(result, dict):
        return JSONResponse(content=jsonable_encoder(result))

    buffer, content_type, filename = result
    return StreamingResponse(buffer, media_type=content_type, headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })


@router.post("/role-permission-report")
async def role_permissions_report(
    filters: RolePermissionReportFilter,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Admins:read"], use_cache=False)
):
    """
    Generates Role Permissions report with filters, ordering, pagination, and export options.
    Pagination applies only when both limit>0 and offset>0.
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


@router.post("/sessions-report")
async def sessions_report(
    filters: SessionsReportFilter,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Sessions:read"], use_cache=False)

):
    """
    Request body: SessionsReportFilter
    Returns JSON list or downloadable CSV/Excel/PDF.
    Pagination is skipped if either limit==0 or offset==0 (i.e., applied only when limit>0 and offset>0).
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


@router.post("/transactions-report")
async def transactions_report(
    filters: TransactionsReportFilter,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Recharge:read"], use_cache=False)

):
    """
    Request body: TransactionsReportFilter
    Returns JSON list or downloadable CSV/Excel/PDF.
    Pagination is skipped if either limit==0 or offset==0 (i.e., applied only when limit>0 and offset>0).
    """
    result = await generate_transactions_report(session, filters)

    if isinstance(result, list) or isinstance(result, dict):
        return JSONResponse(content=jsonable_encoder(result))

    buffer, content_type, filename = result
    return StreamingResponse(buffer, media_type=content_type, headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })


@router.post("/archived-users-report")
async def users_archive_report(
    filters: UsersArchiveFilter,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Users:read"], use_cache=False)

):
    """
    Request body: UsersArchiveFilter
    Returns JSON list or downloadable CSV/Excel/PDF.
    Pagination is applied only when both limit>0 and offset>0. Otherwise returns all results / exports all results.
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


@router.post("/report")
async def users_report(
    filters: UsersReportFilter,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Users:read"], use_cache=False)

):
    """
    Request body: UsersReportFilter
    Returns JSON list or downloadable CSV/Excel/PDF.
    Pagination applied only when both limit>0 and offset>0. Otherwise skip pagination.
    """
    result = await generate_users_report(session, filters)

    if isinstance(result, list) or isinstance(result, dict):
        return JSONResponse(content=jsonable_encoder(result))

    buffer, content_type, filename = result
    return StreamingResponse(buffer, media_type=content_type, headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })