from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from ....schemas.reports import AdminReportFilter, AutoPayReportFilter, BackupReportFilter, CurrentActivePlansFilter
from ....services.reports import generate_admin_report, generate_autopay_report, generate_backup_report, generate_current_active_plans_report
from ....core.database import get_db


router = APIRouter()

@router.post("/admins-report")
async def admin_report(
    filters: AdminReportFilter, session=Depends(get_db)
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
    session: AsyncSession = Depends(get_db)
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