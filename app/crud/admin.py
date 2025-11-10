from sqlalchemy import select, update, desc, asc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.admins import Admin
from ..models.roles import Role
from ..schemas.admin import AdminCreate, AdminUpdate, AdminListFilters
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import Sequence
from datetime import datetime

async def get_admin_by_phone(db: AsyncSession, phone: str):
    """
    Retrieve an admin by phone number.

    Args:
        db (AsyncSession): Async database session.
        phone (str): Phone number to search for.

    Returns:
        Optional[Admin]: Admin instance if found, otherwise None.
    """
    result = await db.execute(select(Admin).where(Admin.phone_number == phone))
    return result.scalars().first()

async def get_admin_role_by_phone(db: AsyncSession, phone: str):
    """
    Retrieve an admin's role information by phone number.

    Args:
        db (AsyncSession): Async database session.
        phone (str): Phone number of the admin.

    Returns:
        Optional[Role]: Role instance if admin exists and has a role, otherwise None.
    """
    result = await db.execute(
        select(Admin)
        .options(selectinload(Admin.role))  
        .where(Admin.phone_number == phone)
    )
    admin = result.scalars().first()
    if admin and getattr(admin, "role", None):
        return admin.role
    return None

async def get_admins(db: AsyncSession, filters: AdminListFilters) -> Sequence[Admin]:
    """
    List admins with filtering, sorting and pagination.

    Args:
        db (AsyncSession): Async database session.
        filters (AdminListFilters): Filtering, sorting and pagination options.

    Returns:
        Sequence[Admin]: List of Admin instances matching the filters.
    """
    stmt = select(Admin).options(selectinload(Admin.role))
    if filters.name:
        stmt = stmt.where(Admin.name.ilike(f"%{filters.name}%"))
    if filters.email:
        stmt = stmt.where(Admin.email.ilike(f"%{filters.email}%"))
    if filters.phone_number:
        stmt = stmt.where(Admin.phone_number.ilike(f"%{filters.phone_number}%"))
    if filters.role_name:
        stmt = stmt.where(Role.role_name.ilike(f"%{filters.role_name}%"))
    if filters.sort_by:
        column = getattr(Admin, filters.sort_by, None)
        if column is not None:
            stmt = stmt.order_by(desc(column) if filters.sort_order == "desc" else asc(column))
    else:
        stmt = stmt.order_by(desc(Admin.created_at))
    stmt = stmt.offset(filters.skip).limit(filters.limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_admin_by_id(db: AsyncSession, admin_id: int):
    """
    Retrieve an admin by their primary key.

    Args:
        db (AsyncSession): Async database session.
        admin_id (int): ID of the admin to retrieve.

    Returns:
        Optional[Admin]: Admin instance if found, otherwise None.
    """
    result = await db.execute(select(Admin).where(Admin.admin_id == admin_id))
    return result.scalar_one_or_none()

async def create_admin(db: AsyncSession, admin_data: AdminCreate):
    """
    Create a new admin record.

    Validates that the phone number is not already in use and resolves role_name
    to a role_id before persisting.

    Args:
        db (AsyncSession): Async database session.
        admin_data (AdminCreate): Pydantic schema with admin creation data.

    Returns:
        Admin: The newly created Admin instance.

    Raises:
        HTTPException: 400 if phone number already exists or role not found;
            404 if specified role does not exist.
    """
    try:
        result = await db.execute(
            select(Admin).where((Admin.phone_number == admin_data.phone_number))
        )
        existing_admin = result.scalars().first()
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin with this phone number already exists",
            )

        data = admin_data.model_dump()

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

        new_admin = Admin(**data)
        new_admin.created_at = datetime.now()
        db.add(new_admin)
        await db.commit()
        await db.refresh(new_admin)

        return new_admin

    except IntegrityError as e:
        await db.rollback()
        if "Admins_phone_number_key" in str(e.orig):
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
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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

async def delete_admin_by_id(db: AsyncSession, admin_id: int):
    admin = await get_admin_by_id(db, admin_id=admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    await db.delete(admin)
    await db.commit()
    return {"message": f"Admin with id {admin_id} deleted"}

async def update_admin_by_phone(db: AsyncSession, phone_number: str, admin_data: AdminUpdate):
    try:
        admin = await get_admin_by_phone(db, phone_number)
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")

        data = admin_data.model_dump(exclude_unset=True)

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

        for key, value in data.items():
            setattr(admin, key, value)
        admin.updated_at = datetime.now()

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
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid input: {str(e)}",
        )

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )

    except HTTPException:
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )

async def update_admin(db: AsyncSession, admin_id: int, admin_data):
    try:
        data = admin_data.model_dump(exclude_unset=True)

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
        updated_admin.updated_at = datetime.now()
        await db.commit()
        return updated_admin

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
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid input: {str(e)}",
        )

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )

    except HTTPException:
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )