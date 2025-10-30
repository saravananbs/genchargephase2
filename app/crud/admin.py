# crud/admins.py
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.admins import Admin
from ..models.roles import Role
from ..schemas.admin import AdminCreate, AdminUpdate, AdminSelfUpdate
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

async def get_admin_by_phone(db: AsyncSession, phone: str):
    result = await db.execute(select(Admin).where(Admin.phone_number == phone))
    return result.scalars().first()

async def get_admin_role_by_phone(db: AsyncSession, phone: str):
    result = await db.execute(
        select(Admin)
        .options(selectinload(Admin.role))  # ✅ eager load role
        .where(Admin.phone_number == phone)
    )
    admin = result.scalars().first()
    if admin and getattr(admin, "role", None):
        return admin.role
    return None




# --- Get Admins ---
async def get_admins(db: AsyncSession):
    result = await db.execute(select(Admin).options(selectinload(Admin.role)))
    return result.scalars().all()


async def get_admin_by_id(db: AsyncSession, admin_id: int):
    result = await db.execute(select(Admin).where(Admin.admin_id == admin_id))
    return result.scalar_one_or_none()


# --- Create Admin ---
async def create_admin(db: AsyncSession, admin_data: AdminCreate):
    try:
        # ✅ Check for duplicate email or phone before insert
        result = await db.execute(
            select(Admin).where(
                (Admin.email == admin_data.email)
                | (Admin.phone_number == admin_data.phone_number)
            )
        )
        existing_admin = result.scalars().first()
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin with this email or phone number already exists",
            )

        data = admin_data.model_dump()

        # ✅ Handle role_name → role_id mapping
        if "role_name" in data and data["role_name"]:
            role_result = await db.execute(
                select(Role).where(Role.role_name == data["role_name"])
            )
            role = role_result.scalar_one_or_none()

            if not role:
                all_roles = await db.execute(select(Role.role_name))
                roles_list = [r for (r,) in all_roles.all()]
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "Role not found", "available_roles": roles_list},
                )

            data["role_id"] = role.role_id
            del data["role_name"]

        # ✅ Create new admin
        new_admin = Admin(**data)
        db.add(new_admin)
        await db.commit()
        await db.refresh(new_admin)

        return new_admin

    except IntegrityError as e:
        await db.rollback()
        if "Admins_email_key" in str(e.orig):
            detail = "Email already exists"
        elif "Admins_phone_number_key" in str(e.orig):
            detail = "Phone number already exists"
        else:
            detail = "Duplicate or integrity error occurred"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid input: {str(e)}",
        )

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )




# --- Delete Admin by phone ---
async def delete_admin_by_phone(db: AsyncSession, phone_number: str):
    admin = await get_admin_by_phone(db, phone_number)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    await db.delete(admin)
    await db.commit()
    return {"message": f"Admin with phone {phone_number} deleted"}


# --- Update Admin by phone (includes role name check) ---
async def update_admin_by_phone(db: AsyncSession, phone_number: str, admin_data: AdminUpdate):
    try:
        admin = await get_admin_by_phone(db, phone_number)
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")

        data = admin_data.model_dump(exclude_unset=True)

        # ✅ Handle role_name → role_id resolution
        if "role_name" in data and data["role_name"]:
            role_result = await db.execute(
                select(Role).where(Role.role_name == data["role_name"])
            )
            role = role_result.scalar_one_or_none()
            if not role:
                all_roles = await db.execute(select(Role.role_name))
                roles_list = [r for (r,) in all_roles.all()]
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "Role not found",
                        "available_roles": roles_list,
                    },
                )
            data["role_id"] = role.role_id
            del data["role_name"]

        # ✅ Apply updates
        for key, value in data.items():
            setattr(admin, key, value)

        await db.commit()
        await db.refresh(admin)
        return admin

    except IntegrityError as e:
        await db.rollback()
        if "Admins_email_key" in str(e.orig):
            detail = "Email already exists"
        elif "Admins_phone_number_key" in str(e.orig):
            detail = "Phone number already exists"
        else:
            detail = "Duplicate or integrity error occurred"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid input: {str(e)}",
        )

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )

    except HTTPException:
        # Already well-formed; re-raise to preserve status code
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


# --- Generic update by ID (used for /admin/me) ---
async def update_admin(db: AsyncSession, admin_id: int, admin_data):
    try:
        data = admin_data.model_dump(exclude_unset=True)

        # ✅ Update the admin record
        query = (
            update(Admin)
            .where(Admin.admin_id == admin_id)
            .values(**data)
            .returning(Admin)
        )
        result = await db.execute(query)
        updated_admin = result.scalar_one_or_none()

        if not updated_admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found",
            )

        await db.commit()
        return updated_admin

    # --- Unique constraint or duplicate key errors ---
    except IntegrityError as e:
        await db.rollback()

        if "Admins_email_key" in str(e.orig):
            detail = "Email already exists"
        elif "Admins_phone_number_key" in str(e.orig):
            detail = "Phone number already exists"
        else:
            detail = "Duplicate or integrity error occurred"

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

    # --- Invalid input / schema mismatch ---
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid input: {str(e)}",
        )

    # --- General SQLAlchemy-related issues ---
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )

    # --- Re-raise FastAPI's own HTTP exceptions (like 404) ---
    except HTTPException:
        raise

    # --- Catch any other unhandled Python-level errors ---
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )