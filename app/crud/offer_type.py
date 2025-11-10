from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc, desc
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from ..models.offer_types import OfferType
from ..schemas.offer_group import OfferTypeCreate, OfferTypeUpdate, OfferTypeFilter

# CREATE
async def create_offer_type(db: AsyncSession, data: OfferTypeCreate):
    """
    Create a new OfferType record.

    Args:
        db (AsyncSession): Async database session.
        data (OfferTypeCreate): Pydantic schema with offer type fields.

    Returns:
        OfferType: The created OfferType ORM instance.

    Raises:
        HTTPException: If a uniqueness constraint is violated.
    """
    new_offer_type = OfferType(**data.model_dump())
    db.add(new_offer_type)
    try:
        await db.commit()
        await db.refresh(new_offer_type)
        return new_offer_type
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offer type name must be unique."
        )

# READ BY ID
async def get_offer_type(db: AsyncSession, offer_type_id: int):
    """
    Retrieve an OfferType by ID.

    Args:
        db (AsyncSession): Async database session.
        offer_type_id (int): Primary key of the offer type.

    Returns:
        Optional[OfferType]: OfferType instance if found, otherwise None.
    """
    result = await db.execute(select(OfferType).where(OfferType.offer_type_id == offer_type_id))
    return result.scalar_one_or_none()

# READ LIST (with pagination, filtering, ordering)
async def get_offer_types(db: AsyncSession, filters: OfferTypeFilter):
    """
    List offer types with optional search, ordering and pagination.

    Args:
        db (AsyncSession): Async database session.
        filters (OfferTypeFilter): Filtering and pagination parameters.

    Returns:
        List[OfferType]: Matching OfferType instances.
    """
    query = select(OfferType)
    if filters.search:
        query = query.where(OfferType.offer_type_name.ilike(f"%{filters.search}%"))
    order_column = getattr(OfferType, filters.order_by, OfferType.offer_type_id)
    if filters.order_dir.lower() == "desc":
        query = query.order_by(desc(order_column))
    else:
        query = query.order_by(asc(order_column))
    query = query.offset(filters.offset).limit(filters.limit)
    result = await db.execute(query)
    return result.scalars().all()

# UPDATE
async def update_offer_type(db: AsyncSession, offer_type_id: int, data: OfferTypeUpdate):
    """
    Update fields of an existing OfferType.

    Args:
        db (AsyncSession): Async database session.
        offer_type_id (int): ID of the OfferType to update.
        data (OfferTypeUpdate): Fields to update (exclude_unset applied).

    Returns:
        OfferType: The updated OfferType instance.

    Raises:
        HTTPException: If OfferType not found or integrity error occurs.
    """
    offer_type = await get_offer_type(db, offer_type_id)
    if not offer_type:
        raise HTTPException(status_code=404, detail="Offer type not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(offer_type, field, value)
    try:
        await db.commit()
        await db.refresh(offer_type)
        return offer_type
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offer type name must be unique."
        )

# DELETE
async def delete_offer_type(db: AsyncSession, offer_type_id: int):
    """
    Delete an OfferType by ID.

    Args:
        db (AsyncSession): Async database session.
        offer_type_id (int): ID of the OfferType to delete.

    Raises:
        HTTPException: If OfferType not found or deletion violates integrity constraints.
    """
    offer_type = await get_offer_type(db, offer_type_id)
    if not offer_type:
        raise HTTPException(status_code=404, detail="Offer type not found")
    await db.delete(offer_type)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Cannot delete offer type — it is referenced by existing offers."
        )
