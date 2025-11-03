# /crud/offer.py
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc, desc, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from ..models.offers import Offer
from ..models.offer_types import OfferType  # adjust imports to your project layout
from ..schemas.offer import OfferCreate, OfferUpdate, OfferFilter

# CREATE
async def create_offer(db: AsyncSession, payload: OfferCreate, created_by: int):
    offer = Offer(**payload.model_dump(), created_by=created_by)
    db.add(offer)
    try:
        await db.commit()
        await db.refresh(offer, attribute_names=["offer_type"])
        result = await db.execute(
            select(Offer).options(selectinload(Offer.offer_type)).where(Offer.offer_id == offer.offer_id)
        )
        offer = result.scalars().first()
        return offer
    except IntegrityError as e:
        await db.rollback()
        msg = str(e.orig).lower()
        if "foreign key" in msg or "referenced" in msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid offer_type_id — referenced OfferType does not exist."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error while creating offer."
        )
    
    
# GET by id
async def get_offer_by_id(db: AsyncSession, offer_id: int) -> Optional[Offer]:
    result = await db.execute(
        select(Offer)
        .options(selectinload(Offer.offer_type))
        .where(Offer.offer_id == offer_id)
    )
    return result.scalar_one_or_none()

# LIST (with filters/pagination/order) for admin
async def list_offers(db: AsyncSession, filters: OfferFilter) -> List[Offer]:
    q = select(Offer).options(selectinload(Offer.offer_type))

    if filters.search:
        q = q.where(
            or_(
                Offer.offer_name.ilike(f"%{filters.search}%"),
                Offer.description.ilike(f"%{filters.search}%")
            )
        )
    if filters.offer_type_id is not None:
        q = q.where(Offer.offer_type_id == filters.offer_type_id)
    if filters.is_special is not None:
        q = q.where(Offer.is_special == filters.is_special)
    if filters.status is not None:
        q = q.where(Offer.status == filters.status)
    allowed = {"offer_id", "offer_name", "offer_validity", "created_at"}
    if filters.order_by not in allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order_by field")
    col = getattr(Offer, filters.order_by)
    q = q.order_by(desc(col) if filters.order_dir == "desc" else asc(col))

    offset = (filters.page - 1) * filters.limit
    q = q.offset(offset).limit(filters.limit)

    res = await db.execute(q)
    return res.scalars().all()

# LIST public (active offers only) - similar but restricts fields later in response
async def list_public_offers(db: AsyncSession, filters: OfferFilter) -> List[Offer]:
    q = select(Offer).options(selectinload(Offer.offer_type)).where(Offer.status == "active")

    if filters.search:
        q = q.where(Offer.offer_name.ilike(f"%{filters.search}%"))
    if filters.offer_type_id is not None:
        q = q.where(Offer.offer_type_id == filters.offer_type_id)
    if filters.is_special is not None:
        q = q.where(Offer.is_special == filters.is_special)

    allowed = {"offer_id", "offer_name", "offer_validity", "created_at"}
    if filters.order_by not in allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order_by field")
    col = getattr(Offer, filters.order_by)
    q = q.order_by(desc(col) if filters.order_dir == "desc" else asc(col))

    offset = (filters.page - 1) * filters.limit
    q = q.offset(offset).limit(filters.limit)

    res = await db.execute(q)
    return res.scalars().all()

# UPDATE
async def update_offer(db: AsyncSession, offer_id: int, payload: OfferUpdate):
    offer = await get_offer_by_id(db, offer_id)
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(offer, k, v)

    try:
        await db.commit()
        await db.refresh(offer)
        return offer
    except IntegrityError as e:
        await db.rollback()
        msg = str(e.orig).lower()
        if "foreign key" in msg or "referenced" in msg:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid offer_type_id — referenced OfferType does not exist.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Integrity error while updating offer.")

# DELETE
async def delete_offer(db: AsyncSession, offer_id: int):
    offer = await get_offer_by_id(db, offer_id)
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
    try:
        await db.delete(offer)
        await db.commit()
        return
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot delete offer — it is referenced by other records.")
