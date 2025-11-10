from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.ext.asyncio import AsyncSession
from ....core.database import get_db
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes
from ....schemas.admin import AdminCreate, AdminUpdate, AdminOut, AdminSelfUpdate, AdminListFilters
from ....crud import admin as admin_crud
from typing import List

router = APIRouter()

# ✅ GET /admin — Get current logged-in admin details
@router.get("/me", response_model=AdminOut)
async def get_self_admin(
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Admin_me:read"])
):
    """
    Retrieve the current logged-in admin's profile information.
    
    This endpoint allows an authenticated admin to view their own profile details
    including name, email, phone, role, and administrative permissions. Used for
    displaying admin profile in dashboard and settings.
    
    Security:
        - Requires valid JWT access token
        - Scope: Admin_me:read
        - Only admin users can access this endpoint
    
    Returns:
        AdminOut: Admin profile object containing:
            - admin_id (int): Unique admin identifier
            - name (str): Admin's full name
            - email (str): Admin's email address
            - phone (str): Admin's phone number
            - role_id (int): Role assigned to admin
            - created_at (datetime): Account creation timestamp
            - updated_at (datetime): Last profile update timestamp
        
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Admin_me:read scope
        HTTPException(404): Admin profile not found in database
    
    Example:
        Request:
            GET /admin/me
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            {
                "admin_id": 1,
                "name": "John Admin",
                "email": "john@gencharge.com",
                "phone": "+919876543210",
                "role_id": 1,
                "created_at": "2024-01-10T10:00:00Z",
                "updated_at": "2024-01-15T14:30:00Z"
            }
    """
    admin = await admin_crud.get_admin_by_id(db, current_user.admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin


# ✅ PATCH /admin — Update self (without role or phone change)
@router.patch("/me", response_model=AdminOut)
async def update_self_admin(
    data: AdminSelfUpdate,
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Admin_me:edit"])
):
    """
    Update the current admin's profile (limited fields).
    
    Allows an authenticated admin to update their own profile information with
    restrictions. Phone and role changes are not allowed through this endpoint
    (require higher privilege operations). Admins can update name and email.
    
    Security:
        - Requires valid JWT access token
        - Scope: Admin_me:edit
        - Admins can only update their own profile
        - Phone and role changes rejected
    
    Request Body:
        AdminSelfUpdate (JSON):
            - name (str, optional): Admin's full name (1-100 chars)
            - email (str, optional): Email address (valid email format)
            - password (str, optional): New password (min 8 chars, hashed before storage)
    
    Returns:
        AdminOut: Updated admin profile object with all current details
        
    Raises:
        HTTPException(400): Invalid data format or validation error
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Admin_me:edit scope
        HTTPException(404): Admin profile not found
        HTTPException(409): Email already in use by another admin
    
    Example:
        Request:
            PATCH /admin/me
            Headers: Authorization: Bearer <jwt_token>
            Body:
            {
                "name": "John Admin Updated",
                "email": "john.updated@gencharge.com"
            }
        
        Response (200 OK):
            {
                "admin_id": 1,
                "name": "John Admin Updated",
                "email": "john.updated@gencharge.com",
                "phone": "+919876543210",
                "role_id": 1,
                "created_at": "2024-01-10T10:00:00Z",
                "updated_at": "2024-01-20T09:15:00Z"
            }
    """
    updated_admin = await admin_crud.update_admin(db, current_user.admin_id, data)
    return updated_admin


# ✅ GET /admins — List all admins
@router.get("/", response_model=List[AdminOut])
async def list_admins(
    db = Depends(get_db),
    filters: AdminListFilters = Depends(),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Admins:read"])
):
    """
    List all admins with optional filtering.
    
    Retrieves a list of all system admins with support for filtering and pagination.
    Used by super-admins to manage admin team and monitor role assignments. Supports
    filtering by role, status, phone number, and email search.
    
    Security:
        - Requires valid JWT access token
        - Scope: Admins:read
        - Typically restricted to super-admin or platform admin roles
    
    Query Parameters (Filters):
        - search (str, optional): Search by name, email, or phone (LIKE pattern)
        - role_id (int, optional): Filter by specific role
        - created_after (datetime, optional): Filter admins created after date
        - created_before (datetime, optional): Filter admins created before date
        - limit (int, optional): Rows per page (default: 50, max: 1000, 0 = all)
        - offset (int, optional): Pagination offset (default: 0)
    
    Returns:
        List[AdminOut]: Array of admin profile objects, each containing:
            - admin_id (int): Unique identifier
            - name (str): Admin name
            - email (str): Email address
            - phone (str): Phone number
            - role_id (int): Assigned role
            - created_at (datetime): Creation timestamp
            - updated_at (datetime): Last update timestamp
        
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Admins:read scope
        HTTPException(400): Invalid filter parameters
    
    Example:
        Request:
            GET /admin/?search=john&role_id=1&limit=20&offset=0
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            [
                {
                    "admin_id": 1,
                    "name": "John Admin",
                    "email": "john@gencharge.com",
                    "phone": "+919876543210",
                    "role_id": 1,
                    "created_at": "2024-01-10T10:00:00Z",
                    "updated_at": "2024-01-15T14:30:00Z"
                },
                {
                    "admin_id": 2,
                    "name": "John Support",
                    "email": "john.support@gencharge.com",
                    "phone": "+919876543211",
                    "role_id": 2,
                    "created_at": "2024-01-12T12:00:00Z",
                    "updated_at": "2024-01-18T11:20:00Z"
                }
            ]
    """
    admins = await admin_crud.get_admins(db, filters)
    return [AdminOut.model_validate(admin, from_attributes=True) for admin in admins]


# ✅ POST /admins — Create a new admin
@router.post("/", response_model=AdminOut)
async def create_admin(
    admin_data: AdminCreate,
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Admins:write"])
):
    """
    Create a new admin account.
    
    Allows authorized users (typically super-admin) to create new admin accounts
    for the system. Automatically sends initial credentials and setup instructions
    to the provided email. New admin must reset password on first login.
    
    Security:
        - Requires valid JWT access token
        - Scope: Admins:write
        - Only super-admin can create new admins
        - Credentials are sent securely via email
    
    Request Body:
        AdminCreate (JSON):
            - name (str): Admin's full name (1-100 chars, required)
            - email (str): Email address (valid format, must be unique)
            - phone (str): Phone number (E.164 format, must be unique)
            - role_id (int): ID of role to assign (must exist in system)
            - password (str, optional): Initial password (auto-generated if not provided)
    
    Returns:
        AdminOut: Newly created admin profile with:
            - admin_id (int): Assigned ID
            - name (str): Admin name
            - email (str): Email address
            - phone (str): Phone number
            - role_id (int): Assigned role
            - created_at (datetime): Creation timestamp
            - updated_at (datetime): Last update timestamp
        
    Raises:
        HTTPException(400): Invalid admin data or validation failed
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Admins:write scope
        HTTPException(409): Email or phone already registered
        HTTPException(422): Role ID not found or invalid
    
    Example:
        Request:
            POST /admin/
            Headers: Authorization: Bearer <jwt_token>
            Body:
            {
                "name": "Alice Manager",
                "email": "alice@gencharge.com",
                "phone": "+919876543212",
                "role_id": 2
            }
        
        Response (201 Created):
            {
                "admin_id": 3,
                "name": "Alice Manager",
                "email": "alice@gencharge.com",
                "phone": "+919876543212",
                "role_id": 2,
                "created_at": "2024-01-20T10:30:00Z",
                "updated_at": "2024-01-20T10:30:00Z"
            }
    """
    return await admin_crud.create_admin(db, admin_data)


# ✅ DELETE /admins/{phone_number} — Delete an admin
@router.delete("/{admin_id}")
async def delete_admin(
    admin_id: int,
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Admins:delete"])
):
    """
    Delete an admin account.
    
    Removes an admin from the system. This action is permanent and will:
    - Revoke all active sessions
    - Revoke all API tokens
    - Remove admin from all assigned roles
    - Prevent future logins
    
    Cannot delete the last super-admin account to prevent system lockout.
    
    Security:
        - Requires valid JWT access token
        - Scope: Admins:delete
        - Only super-admin can delete admin accounts
        - Requires confirmation and logging
    
    Path Parameters:
        - admin_id (int): ID of admin account to delete (must exist)
    
    Returns:
        dict: Status confirmation with deleted admin info:
            {
                "message": "Admin deleted successfully",
                "admin_id": <int>,
                "deleted_at": <datetime>
            }
        
    Raises:
        HTTPException(400): Cannot delete last super-admin account
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Admins:delete scope
        HTTPException(404): Admin with given ID not found
        HTTPException(409): Admin has active sessions - force logout first
    
    Example:
        Request:
            DELETE /admin/3
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            {
                "message": "Admin deleted successfully",
                "admin_id": 3,
                "deleted_at": "2024-01-20T11:00:00Z"
            }
    """
    return await admin_crud.delete_admin_by_id(db, admin_id=admin_id)


# ✅ PATCH /admins/{phone_number} — Update admin info and role
@router.patch("/{admin_id}", response_model=AdminOut)
async def update_admin(
    admin_id: int,
    data: AdminUpdate,
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Admins:edit"])
):
    """
    Update an admin's profile and role.
    
    Allows super-admin to modify another admin's details including name, email,
    phone, and most importantly role assignment. Can promote/demote admins to
    different roles and permission levels. Changes are effective immediately.
    
    Security:
        - Requires valid JWT access token
        - Scope: Admins:edit
        - Only super-admin can update other admins
        - Cannot self-demote from super-admin role
        - All changes are logged for audit
    
    Path Parameters:
        - admin_id (int): ID of admin to update (must exist)
    
    Request Body:
        AdminUpdate (JSON):
            - name (str, optional): Admin's full name (1-100 chars)
            - email (str, optional): Email address (must be unique if changed)
            - phone (str, optional): Phone number (E.164 format, must be unique)
            - role_id (int, optional): New role to assign (must exist in system)
            - status (str, optional): Account status (active/inactive/suspended)
    
    Returns:
        AdminOut: Updated admin profile containing all current details
        
    Raises:
        HTTPException(400): Invalid update data or validation error
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Admins:edit scope
        HTTPException(404): Admin with given ID not found
        HTTPException(409): Email/phone already in use or role not found
        HTTPException(422): Cannot self-demote from super-admin
    
    Example:
        Request:
            PATCH /admin/2
            Headers: Authorization: Bearer <jwt_token>
            Body:
            {
                "name": "Alice Manager Updated",
                "role_id": 3,
                "status": "active"
            }
        
        Response (200 OK):
            {
                "admin_id": 2,
                "name": "Alice Manager Updated",
                "email": "alice@gencharge.com",
                "phone": "+919876543212",
                "role_id": 3,
                "status": "active",
                "created_at": "2024-01-12T12:00:00Z",
                "updated_at": "2024-01-20T11:15:00Z"
            }
    """
    admin = await admin_crud.get_admin_by_id(db=db, admin_id=admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    updated_admin = await admin_crud.update_admin(db, admin_id, data)
    return updated_admin


