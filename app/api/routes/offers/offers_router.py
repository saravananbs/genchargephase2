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
    """
    Create a new offer type/category.
    
    Admin endpoint to create a new offer type that can categorize different promotional offers
    (e.g., "Seasonal", "Birthday", "Loyalty", "Welcome", etc). Offer types help organize
    and manage offers systematically.
    
    Security:
        - Requires valid JWT access token
        - Scope: OfferType:write
        - Admin-only endpoint
    
    Request Body (OfferTypeCreate):
        - name (str): Unique name for the offer type
        - description (str, optional): Description of this offer type
    
    Returns:
        OfferTypeOut: Created offer type object with ID.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing OfferType:write scope.
        HTTPException(400): If name already exists.
    """
    return await offer_type_crud.create_offer_type(db, data)


# READ ALL (with filter, pagination, ordering)
@router.get("/offer_type", response_model=List[OfferTypeOut])
async def list_offer_types(
    filters: OfferTypeFilter = Depends(),
    db=Depends(get_db)
):
    """
    List all offer types with filtering and pagination.
    
    Admin endpoint to retrieve all available offer types.
    
    Security:
        - Requires valid JWT access token
        - Scope: OfferType:read
        - Admin-only endpoint
    
    Query Parameters (OfferTypeFilter):
        - search (str, optional): Search offer type names
        - page (int): Page number (default: 1)
        - limit (int): Records per page (default: 10)
    
    Returns:
        List[OfferTypeOut]: Array of offer type objects.
    """
    return await offer_type_crud.get_offer_types(db, filters)


# READ BY ID
@router.get("/offer_type/{offer_type_id}", response_model=OfferTypeOut)
async def get_offer_type(
    offer_type_id: int,
    db=Depends(get_db)
):
    """
    Retrieve a specific offer type by ID.
    
    Admin endpoint to fetch details of a single offer type.
    
    Path Parameters:
        - offer_type_id (int): Unique identifier of the offer type
    
    Returns:
        OfferTypeOut: Offer type object
        
    Raises:
        HTTPException(404): If offer type not found
    """
    offer_type = await offer_type_crud.get_offer_type(db, offer_type_id)
    if not offer_type:
        raise HTTPException(status_code=404, detail="Offer type not found")
    return offer_type


# UPDATE
@router.put("/offer_type/{offer_type_id}", response_model=OfferTypeOut)
async def update_offer_type(
    offer_type_id: int,
    data: OfferTypeUpdate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    authorized=Security(require_scopes, scopes=["OfferType:edit"])
):
    """
    Update an existing offer type.
    
    Admin endpoint to modify offer type details.
    
    Path Parameters:
        - offer_type_id (int): Unique identifier of the offer type
    
    Request Body (OfferTypeUpdate):
        - name (str, optional): Updated name
        - description (str, optional): Updated description
    
    Returns:
        OfferTypeOut: Updated offer type object
    """
    return await offer_type_crud.update_offer_type(db, offer_type_id, data)


# DELETE
@router.delete("/offer_type/{offer_type_id}")
async def delete_offer_type(
    offer_type_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    authorized=Security(require_scopes, scopes=["OfferType:delete"])
):
    """
    Delete an offer type.
    
    Admin endpoint to permanently remove an offer type from the system.
    
    Path Parameters:
        - offer_type_id (int): Unique identifier of the offer type
    
    Returns:
        dict: Success message confirming deletion
    """
    await offer_type_crud.delete_offer_type(db, offer_type_id)
    return {"detail": "Offer type deleted successfully"}


# Public list for users — only active offers, no created_by/created_at in response
@router.get("/offers/public", response_model=List[PublicOfferResponse])
async def list_public_offers(
    filters: OfferFilter = Depends(),
    db = Depends(get_db),
):
    """
    Retrieve all active offers for users.
    
    Public endpoint (no authentication required) for users to browse active promotional offers
    they can apply to their accounts. Returns only active offers with simplified information
    suitable for user interfaces.
    
    Query Parameters (OfferFilter):
        - search (str, optional): Search offer names/descriptions
        - page (int): Page number (default: 1)
        - limit (int): Records per page (default: 10)
    
    Returns:
        List[PublicOfferResponse]: Array of public offer objects (active only)
    """
    offers = await offer_crud.list_public_offers(db, filters)
    return offers

# Create (admin)
@router.post("/offers", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
async def create_offer(
    payload: OfferCreate,
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Offers:write"])
):
    """
    Create a new promotional offer.
    
    Admin endpoint to create a new offer that users can apply to their accounts or plans.
    Offers can include discounts, free minutes/data, or other benefits.
    
    Security:
        - Requires valid JWT access token
        - Scope: Offers:write
        - Admin-only endpoint
    
    Request Body (OfferCreate):
        - offer_name (str): Name of the offer
        - description (str, optional): Description of benefits
        - discount_percentage (float, optional): Discount percentage (0-100)
        - discount_amount (Decimal, optional): Fixed discount amount
        - offer_type_id (int): Reference to OfferType
        - validity_days (int): How long the offer is valid
        - status (str): 'active' or 'inactive'
    
    Returns:
        OfferResponse: Created offer object (HTTP 201 Created)
        
    Raises:
        HTTPException(403): If missing Offers:write scope
    """
    result = await offer_crud.create_offer(db, payload, created_by=current_user.admin_id)
    return result

# Update (admin)
@router.put("/offers/{offer_id}", response_model=OfferResponse)
async def update_offer(
    offer_id: int,
    payload: OfferUpdate,
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Offers:edit"])
):
    """
    Update an existing offer.
    
    Admin endpoint to modify offer details such as discount, validity, or status.
    Partial updates supported.
    
    Security:
        - Scope: Offers:edit
        - Admin-only endpoint
    
    Path Parameters:
        - offer_id (int): ID of offer to update
    
    Request Body (OfferUpdate):
        - offer_name (str, optional): Updated name
        - discount_percentage (float, optional): Updated discount
        - status (str, optional): 'active' or 'inactive'
    
    Returns:
        OfferResponse: Updated offer object
    """
    return await offer_crud.update_offer(db, offer_id, payload)

# Delete (admin)
@router.delete("/offers/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_offer(
    offer_id: int,
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Offers:delete"])
):
    """
    Delete an offer.
    
    Admin endpoint to permanently remove an offer from the system.
    
    Security:
        - Scope: Offers:delete
        - Admin-only endpoint
    
    Path Parameters:
        - offer_id (int): ID of offer to delete
    
    Returns:
        null: HTTP 204 No Content on success
    """
    await offer_crud.delete_offer(db, offer_id)
    return None

# Get all (admin) with filter/pagination/order
@router.get("/offers", response_model=List[OfferResponse])
async def list_offers(
    filters: OfferFilter = Depends(),
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Offers:read"])
):
    """
    Retrieve all offers with advanced filtering.
    
    Admin endpoint to fetch all offers (active and inactive) with filtering and pagination.
    
    Security:
        - Scope: Offers:read
        - Admin-only endpoint
    
    Query Parameters (OfferFilter):
        - search (str, optional): Search by name/description
        - status (str, optional): Filter by 'active' or 'inactive'
        - page (int): Page number (default: 1)
        - limit (int): Records per page (default: 10)
    
    Returns:
        List[OfferResponse]: Array of offer objects
    """
    offers = await offer_crud.list_offers(db, filters)
    return offers

# Get by id (admin)
@router.get("/offers/{offer_id}", response_model=OfferResponse)
async def get_offer(
    offer_id: int,
    db = Depends(get_db)
):
    """
    Retrieve a specific offer by ID.
    
    Admin endpoint to fetch detailed information about a single offer.
    
    Security:
        - Scope: Offers:read
        - Admin-only endpoint
    
    Path Parameters:
        - offer_id (int): ID of the offer
    
    Returns:
        OfferResponse: Complete offer object
        
    Raises:
        HTTPException(404): If offer not found
    """
    offer = await offer_crud.get_offer_by_id(db, offer_id)
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
    return offer

