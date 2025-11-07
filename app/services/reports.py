import io
import pandas as pd
from typing import List, Tuple, Union
from fastapi.encoders import jsonable_encoder
from ..schemas.reports import (
    AdminReportFilter, AutoPayReportFilter, BackupReportFilter, CurrentActivePlansFilter,
    OfferReportFilter, PlanReportFilter, ReferralReportFilter, RolePermissionReportFilter,
    SessionsReportFilter, TransactionsReportFilter, UsersArchiveFilter, UsersReportFilter
)
from ..crud.reports import (
    get_admin_report, get_autopays, get_backups, get_current_active_plans, get_offers,
    get_plans, get_referrals, get_role_permissions, get_sessions, get_transactions,
    get_users_archive, get_users
)
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


def _row_from_curr_active_plan(a) -> dict:
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
    rows = [_row_from_curr_active_plan(a) for a in objs]

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


def _row_from_offer(o) -> dict:
    # o is an ORM Offer
    return {
        "offer_id": o.offer_id,
        "offer_name": o.offer_name,
        "offer_validity": o.offer_validity,
        "is_special": bool(o.is_special),
        "criteria": o.criteria,
        "description": o.description,
        "created_at": o.created_at,
        "created_by": o.created_by,
        "status": o.status.value if hasattr(o.status, "value") else str(o.status),
        "offer_type_id": getattr(o.offer_type, "offer_type_id", None) if getattr(o, "offer_type", None) else None,
        "offer_type_name": getattr(o.offer_type, "offer_type_name", None) if getattr(o, "offer_type", None) else None,
    }

async def generate_offers_report(
    session: AsyncSession,
    filters: OfferReportFilter
) -> Union[List[dict], Tuple[io.BytesIO, str, str]]:
    offers = await get_offers(session, filters)
    rows = [_row_from_offer(o) for o in offers]

    # If json requested
    if filters.export_type == "none":
        return jsonable_encoder(rows)

    # Build dataframe
    df = pd.DataFrame(rows)

    # CSV
    if filters.export_type == "csv":
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return buf, "text/csv", "offers_report.csv"

    # Excel
    if filters.export_type == "excel":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Offers")
        buf.seek(0)
        return buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "offers_report.xlsx"

    # PDF (simple tabular text)
    if filters.export_type == "pdf":
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Offers Report", ln=True, align="C")
        pdf.ln(6)
        pdf.set_font("Arial", size=9)

        cols = [
            "offer_id", "offer_name", "is_special", "offer_validity", "status", "offer_type_name", "created_at", "created_by"
        ]
        header = " | ".join(cols)
        pdf.multi_cell(0, 6, header)
        pdf.ln(2)

        for r in rows:
            values = []
            for c in cols:
                v = r.get(c, "")
                if v is None:
                    v = ""
                # format datetime
                if hasattr(v, "isoformat"):
                    v = v.isoformat()
                s = str(v)
                if len(s) > 60:
                    s = s[:57] + "..."
                values.append(s)
            pdf.multi_cell(0, 6, " | ".join(values))

        buf = io.BytesIO(pdf.output(dest="S").encode("latin1"))
        buf.seek(0)
        return buf, "application/pdf", "offers_report.pdf"

    # fallback
    return jsonable_encoder(rows)


def _row_from_plan(p) -> dict:
    return {
        "plan_id": p.plan_id,
        "plan_name": p.plan_name,
        "validity": p.validity,
        "most_popular": bool(p.most_popular),
        "plan_type": p.plan_type.value if hasattr(p.plan_type, "value") else str(p.plan_type),
        "group_id": getattr(p.group, "group_id", None) if getattr(p, "group", None) else None,
        "group_name": getattr(p.group, "group_name", None) if getattr(p, "group", None) else None,
        "description": p.description,
        "criteria": p.criteria,
        "created_at": p.created_at,
        "created_by": p.created_by,
        "price": p.price,
        "status": p.status.value if hasattr(p.status, "value") else str(p.status),
    }

async def generate_plans_report(session: AsyncSession, filters: PlanReportFilter) -> Union[List[dict], Tuple[io.BytesIO, str, str]]:
    plans = await get_plans(session, filters)
    rows = [_row_from_plan(p) for p in plans]

    # If JSON requested
    if filters.export_type == "none":
        # jsonable_encoder will convert datetimes/enums
        return jsonable_encoder(rows)

    # Use pandas for tabular exports
    df = pd.DataFrame(rows)

    if filters.export_type == "csv":
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return buf, "text/csv", "plans_report.csv"

    if filters.export_type == "excel":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Plans")
        buf.seek(0)
        return buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "plans_report.xlsx"

    if filters.export_type == "pdf":
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Plans Report", ln=True, align="C")
        pdf.ln(6)
        pdf.set_font("Arial", size=9)

        cols = ["plan_id", "plan_name", "price", "validity", "most_popular", "plan_type", "group_name", "created_at"]
        pdf.multi_cell(0, 6, " | ".join(cols))
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
                if len(s) > 60:
                    s = s[:57] + "..."
                vals.append(s)
            pdf.multi_cell(0, 6, " | ".join(vals))

        buf = io.BytesIO(pdf.output(dest="S").encode("latin1"))
        buf.seek(0)
        return buf, "application/pdf", "plans_report.pdf"

    # fallback
    return jsonable_encoder(rows)


def _row_from_r(r) -> dict:
    """Flatten ORM ReferralReward to dict for JSON/export."""
    return {
        "reward_id": r.reward_id,
        "referrer_id": r.referrer_id,
        "referred_id": r.referred_id,
        "reward_amount": float(r.reward_amount) if r.reward_amount is not None else None,
        "status": r.status,
        "created_at": r.created_at,
        "claimed_at": r.claimed_at,
        "referrer_name": getattr(r.referrer, "name", None) if getattr(r, "referrer", None) else None,
        "referrer_phone": getattr(r.referrer, "phone_number", None) if getattr(r, "referrer", None) else None,
        "referred_name": getattr(r.referred, "name", None) if getattr(r, "referred", None) else None,
        "referred_phone": getattr(r.referred, "phone_number", None) if getattr(r, "referred", None) else None,
    }

async def generate_referral_report(session: AsyncSession, filters: ReferralReportFilter) -> Union[List[dict], Tuple[io.BytesIO, str, str]]:
    rows_orm = await get_referrals(session, filters)
    rows = [_row_from_r(r) for r in rows_orm]

    # JSON (no export)
    if filters.export_type == "none":
        return jsonable_encoder(rows)

    # Build DataFrame for exports
    df = pd.DataFrame(rows)

    if filters.export_type == "csv":
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return buf, "text/csv", "referral_report.csv"

    if filters.export_type == "excel":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Referrals")
        buf.seek(0)
        return buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "referral_report.xlsx"

    if filters.export_type == "pdf":
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Referral Rewards Report", ln=True, align="C")
        pdf.ln(6)
        pdf.set_font("Arial", size=9)

        cols = ["reward_id", "referrer_name", "referred_name", "reward_amount", "status", "created_at", "claimed_at"]
        pdf.multi_cell(0, 6, " | ".join(cols))
        pdf.ln(2)

        for r in rows:
            values = []
            for c in cols:
                v = r.get(c, "")
                if v is None:
                    v = ""
                if hasattr(v, "isoformat"):
                    v = v.isoformat()
                s = str(v)
                if len(s) > 60:
                    s = s[:57] + "..."
                values.append(s)
            pdf.multi_cell(0, 6, " | ".join(values))

        buf = io.BytesIO(pdf.output(dest="S").encode("latin1"))
        buf.seek(0)
        return buf, "application/pdf", "referral_report.pdf"

    # fallback
    return jsonable_encoder(rows)


def _row_from_rp_rep(rp) -> dict:
    return {
        "id": rp.id,
        "role_id": rp.role_id,
        "permission_id": rp.permission_id,
        "role_name": getattr(rp.role, "role_name", None) if getattr(rp, "role", None) else None,
        "resource": getattr(rp.permission, "resource", None) if getattr(rp, "permission", None) else None,
        "read": getattr(rp.permission, "read", None),
        "write": getattr(rp.permission, "write", None),
        "edit": getattr(rp.permission, "edit", None),
        "delete": getattr(rp.permission, "delete", None),
    }

async def generate_role_permission_report(
    session: AsyncSession,
    filters: RolePermissionReportFilter
) -> Union[List[dict], Tuple[io.BytesIO, str, str]]:
    objs = await get_role_permissions(session, filters)
    rows = [_row_from_rp_rep(o) for o in objs]

    if filters.export_type == "none":
        return jsonable_encoder(rows)

    df = pd.DataFrame(rows)

    if filters.export_type == "csv":
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return buf, "text/csv", "role_permissions_report.csv"

    if filters.export_type == "excel":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="RolePermissions")
        buf.seek(0)
        return buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "role_permissions_report.xlsx"

    if filters.export_type == "pdf":
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Role Permissions Report", ln=True, align="C")
        pdf.ln(6)
        pdf.set_font("Arial", size=9)

        cols = ["id", "role_name", "resource", "read", "write", "edit", "delete"]
        pdf.multi_cell(0, 6, " | ".join(cols))
        pdf.ln(2)

        for row in rows:
            values = [str(row.get(c, "")) for c in cols]
            pdf.multi_cell(0, 6, " | ".join(values))

        buf = io.BytesIO(pdf.output(dest="S").encode("latin1"))
        buf.seek(0)
        return buf, "application/pdf", "role_permissions_report.pdf"

    return jsonable_encoder(rows)


def _row_from_session(s) -> dict:
    return {
        "session_id": str(s.session_id),
        "user_id": s.user_id,
        "refresh_token": s.refresh_token,
        "jti": str(s.jti),
        "refresh_token_expires_at": s.refresh_token_expires_at,
        "login_time": s.login_time,
        "last_active": s.last_active,
        "is_active": bool(s.is_active),
        "revoked_at": s.revoked_at,
    }

async def generate_sessions_report(
    session: AsyncSession,
    filters: SessionsReportFilter
) -> Union[List[dict], Tuple[io.BytesIO, str, str]]:
    objs = await get_sessions(session, filters)
    rows = [_row_from_session(o) for o in objs]

    # JSON response
    if filters.export_type == "none":
        return jsonable_encoder(rows)

    # Build a DataFrame for CSV/Excel
    df = pd.DataFrame(rows)

    if filters.export_type == "csv":
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return buf, "text/csv", "sessions_report.csv"

    if filters.export_type == "excel":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Sessions")
        buf.seek(0)
        return buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "sessions_report.xlsx"

    if filters.export_type == "pdf":
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Sessions Report", ln=True, align="C")
        pdf.ln(6)
        pdf.set_font("Arial", size=9)

        cols = ["session_id", "user_id", "refresh_token_expires_at", "login_time", "last_active", "is_active", "revoked_at"]
        pdf.multi_cell(0, 6, " | ".join(cols))
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
                if len(s) > 120:
                    s = s[:117] + "..."
                vals.append(s)
            pdf.multi_cell(0, 6, " | ".join(vals))

        buf = io.BytesIO(pdf.output(dest="S").encode("latin1"))
        buf.seek(0)
        return buf, "application/pdf", "sessions_report.pdf"

    # fallback
    return jsonable_encoder(rows)


def _row_from_txn(t) -> dict:
    return {
        "txn_id": t.txn_id,
        "user_id": t.user_id,
        "category": t.category.value if hasattr(t.category, "value") else str(t.category),
        "txn_type": t.txn_type.value if hasattr(t.txn_type, "value") else str(t.txn_type),
        "amount": float(t.amount) if t.amount is not None else None,
        "service_type": t.service_type.value if hasattr(t.service_type, "value") else (t.service_type if t.service_type is not None else None),
        "plan_id": t.plan_id,
        "offer_id": t.offer_id,
        "from_phone_number": t.from_phone_number,
        "to_phone_number": t.to_phone_number,
        "source": t.source.value if hasattr(t.source, "value") else str(t.source),
        "status": t.status.value if hasattr(t.status, "value") else str(t.status),
        "payment_method": t.payment_method.value if hasattr(t.payment_method, "value") else (t.payment_method if t.payment_method is not None else None),
        "payment_transaction_id": t.payment_transaction_id,
        "created_at": t.created_at,
    }

async def generate_transactions_report(
    session: AsyncSession,
    filters: TransactionsReportFilter
) -> Union[List[dict], Tuple[io.BytesIO, str, str]]:
    objs = await get_transactions(session, filters)
    rows = [_row_from_txn(o) for o in objs]

    # JSON (no export)
    if filters.export_type == "none":
        return jsonable_encoder(rows)

    # Build dataframe for exports
    df = pd.DataFrame(rows)

    if filters.export_type == "csv":
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return buf, "text/csv", "transactions_report.csv"

    if filters.export_type == "excel":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Transactions")
        buf.seek(0)
        return buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "transactions_report.xlsx"

    if filters.export_type == "pdf":
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Transactions Report", ln=True, align="C")
        pdf.ln(6)
        pdf.set_font("Arial", size=9)

        cols = [
            "txn_id", "user_id", "category", "txn_type", "amount", "service_type",
            "source", "status", "payment_method", "payment_transaction_id", "created_at"
        ]
        pdf.multi_cell(0, 6, " | ".join(cols))
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
                if len(s) > 80:
                    s = s[:77] + "..."
                vals.append(s)
            pdf.multi_cell(0, 6, " | ".join(vals))

        buf = io.BytesIO(pdf.output(dest="S").encode("latin1"))
        buf.seek(0)
        return buf, "application/pdf", "transactions_report.pdf"

    # fallback
    return jsonable_encoder(rows)


def _row_from_auser(u) -> dict:
    return {
        "user_id": u.user_id,
        "name": u.name,
        "email": u.email,
        "phone_number": u.phone_number,
        "referral_code": u.referral_code,
        "referee_code": u.referee_code,
        "user_type": u.user_type.value if hasattr(u.user_type, "value") else (u.user_type if u.user_type is not None else None),
        "status": u.status.value if hasattr(u.status, "value") else (u.status if u.status is not None else None),
        "wallet_balance": float(u.wallet_balance) if u.wallet_balance is not None else None,
        "created_at": u.created_at,
        "deleted_at": u.deleted_at,
    }

async def generate_users_archive_report(
    session: AsyncSession,
    filters: UsersArchiveFilter
) -> Union[List[dict], Tuple[io.BytesIO, str, str]]:
    objs = await get_users_archive(session, filters)
    rows = [_row_from_auser(u) for u in objs]

    # JSON
    if filters.export_type == "none":
        return jsonable_encoder(rows)

    # DataFrame for exports
    df = pd.DataFrame(rows)

    if filters.export_type == "csv":
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return buf, "text/csv", "users_archive_report.csv"

    if filters.export_type == "excel":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="UsersArchive")
        buf.seek(0)
        return buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "users_archive_report.xlsx"

    if filters.export_type == "pdf":
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Users Archive Report", ln=True, align="C")
        pdf.ln(6)
        pdf.set_font("Arial", size=9)

        cols = ["user_id", "name", "email", "phone_number", "user_type", "status", "wallet_balance", "created_at", "deleted_at"]
        pdf.multi_cell(0, 6, " | ".join(cols))
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
                if len(s) > 80:
                    s = s[:77] + "..."
                vals.append(s)
            pdf.multi_cell(0, 6, " | ".join(vals))

        buf = io.BytesIO(pdf.output(dest="S").encode("latin1"))
        buf.seek(0)
        return buf, "application/pdf", "users_archive_report.pdf"

    # fallback
    return jsonable_encoder(rows)


def _row_from_user(u) -> dict:
    return {
        "user_id": u.user_id,
        "name": u.name,
        "email": u.email,
        "phone_number": u.phone_number,
        "referral_code": u.referral_code,
        "referee_code": u.referee_code,
        "user_type": u.user_type.value if hasattr(u.user_type, "value") else (str(u.user_type) if u.user_type is not None else None),
        "status": u.status.value if hasattr(u.status, "value") else (str(u.status) if u.status is not None else None),
        "wallet_balance": float(u.wallet_balance) if u.wallet_balance is not None else None,
        "created_at": u.created_at,
        "updated_at": u.updated_at,
    }

async def generate_users_report(
    session: AsyncSession,
    filters: UsersReportFilter
) -> Union[List[dict], Tuple[io.BytesIO, str, str]]:
    objs = await get_users(session, filters)
    rows = [_row_from_user(u) for u in objs]

    # If JSON requested
    if filters.export_type == "none":
        return jsonable_encoder(rows)

    # build dataframe
    df = pd.DataFrame(rows)

    # CSV
    if filters.export_type == "csv":
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return buf, "text/csv", "users_report.csv"

    # Excel
    if filters.export_type == "excel":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Users")
        buf.seek(0)
        return buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "users_report.xlsx"

    # PDF (simple text table)
    if filters.export_type == "pdf":
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Users Report", ln=True, align="C")
        pdf.ln(6)
        pdf.set_font("Arial", size=9)

        cols = ["user_id","name","email","phone_number","user_type","status","wallet_balance","created_at"]
        pdf.multi_cell(0, 6, " | ".join(cols))
        pdf.ln(2)

        for r in rows:
            vals = []
            for c in cols:
                v = r.get(c, "") or ""
                if hasattr(v, "isoformat"):
                    v = v.isoformat()
                s = str(v)
                if len(s) > 80:
                    s = s[:77] + "..."
                vals.append(s)
            pdf.multi_cell(0, 6, " | ".join(vals))

        buf = io.BytesIO(pdf.output(dest="S").encode("latin1"))
        buf.seek(0)
        return buf, "application/pdf", "users_report.pdf"

    # fallback
    return jsonable_encoder(rows)