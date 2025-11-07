import io
import pandas as pd
from typing import List, Tuple, Union
from fastapi.encoders import jsonable_encoder
from ..schemas.reports import AdminOut, AdminReportFilter, AutoPayReportFilter, BackupReportFilter, CurrentActivePlansFilter
from ..crud.reports import get_admin_report, get_autopays, get_backups, get_current_active_plans
from sqlalchemy.ext.asyncio import AsyncSession
from fpdf import FPDF


async def generate_admin_report(session: AsyncSession, filters: AdminReportFilter):
    admins = await get_admin_report(session, filters)
    data = [
        {
            "Admin ID": a.admin_id,
            "Name": a.name,
            "Email": a.email,
            "Phone": a.phone_number,
            "Role": a.role.role_name if a.role else None,
            "Created At": a.created_at,
            "Updated At": a.updated_at,
        }
        for a in admins
    ]

    if filters.export_type == "none":
        return data

    df = pd.DataFrame(data)

    # Export Handling
    if filters.export_type == "csv":
        buffer = io.BytesIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return buffer, "text/csv", "admin_report.csv"

    elif filters.export_type == "excel":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Admins")
        buffer.seek(0)
        return buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "admin_report.xlsx"

    elif filters.export_type == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 10, txt="Admin Report", ln=True, align="C")
        pdf.ln(10)
        for row in data:
            line = f"{row['Admin ID']} | {row['Name']} | {row['Email']} | {row['Role']}"
            pdf.multi_cell(0, 8, txt=line)
        buffer = io.BytesIO(pdf.output(dest="S").encode("latin1"))
        buffer.seek(0)
        return buffer, "application/pdf", "admin_report.pdf"

    return data


def _row_from_autopay(a) -> dict:
    """Convert ORM autopay row to plain dict for output/export."""
    return {
        "autopay_id": a.autopay_id,
        "user_id": a.user_id,
        "plan_id": a.plan_id,
        "status": a.status,
        "tag": a.tag,
        "phone_number": a.phone_number,
        "next_due_date": a.next_due_date,
        "created_at": a.created_at,
        "plan_name": getattr(a.plan, "plan_name", None) if getattr(a, "plan", None) else None,
        "plan_price": getattr(a.plan, "price", None) if getattr(a, "plan", None) else None,
        "plan_type": getattr(a.plan, "plan_type", None).value if getattr(a, "plan", None) and getattr(a.plan, "plan_type", None) else None,
        "user_name": getattr(a.user, "name", None) if getattr(a, "user", None) else None,
        "user_phone": getattr(a.user, "phone_number", None) if getattr(a, "user", None) else None,
    }


async def generate_autopay_report(
    session: AsyncSession,
    filters: AutoPayReportFilter
) -> Union[List[dict], Tuple[io.BytesIO, str, str]]:
    """
    Returns:
      - if export_type == "none": list[dict] (plain data)
      - else: (buffer, content_type, filename)
    """
    autopays = await get_autopays(session, filters)
    rows = [_row_from_autopay(a) for a in autopays]

    # If user only wants JSON data
    if filters.export_type == "none":
        # Use jsonable_encoder for datetimes, decimals, etc.
        return jsonable_encoder(rows)

    # Otherwise build DataFrame and export
    df = pd.DataFrame(rows)

    if filters.export_type == "csv":
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return buf, "text/csv", "autopay_report.csv"

    if filters.export_type == "excel":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="AutoPays")
        buf.seek(0)
        return buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "autopay_report.xlsx"

    if filters.export_type == "pdf":
        # Simple PDF generation using FPDF (tabular text)
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "AutoPay Report", ln=True, align="C")
        pdf.ln(6)
        pdf.set_font("Arial", size=9)

        # header row
        cols = ["autopay_id", "user_id", "plan_id", "status", "tag", "phone_number", "next_due_date", "plan_name", "plan_price"]
        header = " | ".join(cols)
        pdf.multi_cell(0, 6, header)
        pdf.ln(2)

        for r in rows:
            # build a short line for pdf (truncate long text)
            values = []
            for c in cols:
                v = r.get(c, "")
                if v is None:
                    v = ""
                # format datetimes
                if hasattr(v, "isoformat"):
                    v = v.isoformat()
                s = str(v)
                if len(s) > 40:
                    s = s[:37] + "..."
                values.append(s)
            line = " | ".join(values)
            pdf.multi_cell(0, 6, line)

        buf = io.BytesIO(pdf.output(dest="S").encode("latin1"))
        buf.seek(0)
        return buf, "application/pdf", "autopay_report.pdf"

    # fallback: return JSON
    return jsonable_encoder(rows)


async def generate_backup_report(session: AsyncSession, filters: BackupReportFilter) -> Union[List[dict], Tuple[io.BytesIO, str, str]]:
    backups = await get_backups(session, filters)

    rows = [
        {
            "backup_id": b.backup_id,
            "backup_data": b.backup_data,
            "snapshot_name": b.snapshot_name,
            "storage_url": b.storage_url,
            "backup_status": b.backup_status,
            "size_mb": b.size_mb,
            "description": b.description,
            "details": b.details,
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "created_by": b.created_by
        }
        for b in backups
    ]

    # JSON response
    if filters.export_type == "none":
        return jsonable_encoder(rows)

    # Pandas DataFrame for export
    df = pd.DataFrame(rows)

    # CSV Export
    if filters.export_type == "csv":
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return buf, "text/csv", "backup_report.csv"

    # Excel Export
    if filters.export_type == "excel":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Backups")
        buf.seek(0)
        return buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "backup_report.xlsx"

    # PDF Export
    if filters.export_type == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, txt="Backup Report", ln=True, align="C")
        pdf.set_font("Arial", size=9)
        pdf.ln(5)

        for row in rows:
            line = f"{row['backup_id']} | {row['backup_data']} | {row['backup_status']} | {row['size_mb']} MB | {row['created_at']}"
            pdf.multi_cell(0, 7, line)
            pdf.ln(2)

        buf = io.BytesIO(pdf.output(dest="S").encode("latin1"))
        buf.seek(0)
        return buf, "application/pdf", "backup_report.pdf"

    return jsonable_encoder(rows)


def _row_from_obj(a) -> dict:
    """Flatten ORM object to dict suitable for JSON/export."""
    return {
        "id": a.id,
        "user_id": a.user_id,
        "plan_id": a.plan_id,
        "phone_number": a.phone_number,
        "valid_from": a.valid_from,
        "valid_to": a.valid_to,
        "status": a.status,
        "plan_name": getattr(a.plan, "plan_name", None) if getattr(a, "plan", None) else None,
        "plan_price": getattr(a.plan, "price", None) if getattr(a, "plan", None) else None,
        "plan_type": getattr(a.plan, "plan_type", None).value if getattr(a, "plan", None) and getattr(a.plan, "plan_type", None) else None,
        "user_name": getattr(a.user, "name", None) if getattr(a, "user", None) else None,
        "user_phone": getattr(a.user, "phone_number", None) if getattr(a, "user", None) else None,
    }


async def generate_current_active_plans_report(
    session: AsyncSession,
    filters: CurrentActivePlansFilter
) -> Union[List[dict], Tuple[io.BytesIO, str, str]]:
    objs = await get_current_active_plans(session, filters)
    rows = [_row_from_obj(a) for a in objs]

    # If JSON response requested
    if filters.export_type == "none":
        return jsonable_encoder(rows)

    # else DataFrame + export
    df = pd.DataFrame(rows)

    if filters.export_type == "csv":
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return buf, "text/csv", "current_active_plans_report.csv"

    if filters.export_type == "excel":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="ActivePlans")
        buf.seek(0)
        return buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "current_active_plans_report.xlsx"

    if filters.export_type == "pdf":
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Current Active Plans Report", ln=True, align="C")
        pdf.ln(6)
        pdf.set_font("Arial", size=9)

        cols = ["id", "user_id", "plan_id", "phone_number", "valid_from", "valid_to", "status", "plan_name", "plan_price"]
        header = " | ".join(cols)
        pdf.multi_cell(0, 6, header)
        pdf.ln(2)

        for r in rows:
            vals = []
            for c in cols:
                v = r.get(c, "")
                if v is None:
                    v = ""
                if hasattr(v, "isoformat"):
                    v = v.isoformat()
                s = str(v)
                if len(s) > 45:
                    s = s[:42] + "..."
                vals.append(s)
            pdf.multi_cell(0, 6, " | ".join(vals))

        buf = io.BytesIO(pdf.output(dest="S").encode("latin1"))
        buf.seek(0)
        return buf, "application/pdf", "current_active_plans_report.pdf"

    # fallback
    return jsonable_encoder(rows)

