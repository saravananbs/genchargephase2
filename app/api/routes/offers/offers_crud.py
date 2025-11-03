from fastapi import APIRouter, Depends, HTTPException, Security, status
from typing import List
from ....core.database import get_db
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes
from ....schemas.offer_group import OfferTypeOut, OfferTypeCreate, OfferTypeUpdate, OfferTypeFilter
from ....schemas.offer import OfferCreate, OfferResponse, OfferFilter, OfferUpdate, PublicOfferResponse
from ....crud import offer_type as offer_type_crud
from ....crud import offer as offer_crud

router = APIRouter()

# CREATE
@router.post("/offer_type", response_model=OfferTypeOut)
async def create_offer_type(
    data: OfferTypeCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    authorized=Security(require_scopes, scopes=["OfferType:write"])
):
    return await offer_type_crud.create_offer_type(db, data)


# READ ALL (with filter, pagination, ordering)
@router.get("/offer_type", response_model=List[OfferTypeOut])
async def list_offer_types(
    filters: OfferTypeFilter = Depends(),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    authorized=Security(require_scopes, scopes=["OfferType:read"])
):
    return await offer_type_crud.get_offer_types(db, filters)


# READ BY ID
@router.get("/offer_type/{offer_type_id}", response_model=OfferTypeOut)
async def get_offer_type(
    offer_type_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    authorized=Security(require_scopes, scopes=["OfferType:read"])
):
    offer_type = await offer_type_crud.get_offer_type(db, offer_type_id)
    if not offer_type:
        raise HTTPException(status_code=404, detail="Offer type not found")
    return offer_type


# UPDATE
@router.put("/offer_type{offer_type_id}", response_model=OfferTypeOut)
async def update_offer_type(
    offer_type_id: int,
    data: OfferTypeUpdate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    authorized=Security(require_scopes, scopes=["OfferType:edit"])
):
    return await offer_type_crud.update_offer_type(db, offer_type_id, data)


# DELETE
@router.delete("/offer_type/{offer_type_id}")
async def delete_offer_type(
    offer_type_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    authorized=Security(require_scopes, scopes=["OfferType:delete"])
):
    await offer_type_crud.delete_offer_type(db, offer_type_id)
    return {"detail": "Offer type deleted successfully"}


# Public list for users — only active offers, no created_by/created_at in response
@router.get("/offers/public", response_model=List[PublicOfferResponse])
async def list_public_offers(
    filters: OfferFilter = Depends(),
    db = Depends(get_db),
):
    offers = await offer_crud.list_public_offers(db, filters)
    return offers

# Create (admin)
@router.post("/offers", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
async def create_offer(
    payload: OfferCreate,
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Offers:write"], use_cache=False)
):
    
    result = await offer_crud.create_offer(db, payload, created_by=current_user.admin_id)
    return result

# Update (admin)
@router.put("/offers/{offer_id}", response_model=OfferResponse)
async def update_offer(
    offer_id: int,
    payload: OfferUpdate,
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Offers:edit"], use_cache=False)
):
    return await offer_crud.update_offer(db, offer_id, payload)

# Delete (admin)
@router.delete("/offers/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_offer(
    offer_id: int,
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Offers:delete"], use_cache=False)
):
    await offer_crud.delete_offer(db, offer_id)
    return None

# Get all (admin) with filter/pagination/order
@router.get("/offers", response_model=List[OfferResponse])
async def list_offers(
    filters: OfferFilter = Depends(),
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Offers:read"], use_cache=False)
):
    offers = await offer_crud.list_offers(db, filters)
    return offers

# Get by id (admin)
@router.get("/offers/{offer_id}", response_model=OfferResponse)
async def get_offer(
    offer_id: int,
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Offers:read"], use_cache=False)
):
    offer = await offer_crud.get_offer_by_id(db, offer_id)
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
    return offer

