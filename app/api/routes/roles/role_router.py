# api/routes/roles.py
from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes
from ....core.database import get_db
from ....schemas.role import RoleCreate, RoleUpdate, RoleResponse, PermissionBase, RoleListFilters
from ....crud import role as crud_roles

router = APIRouter()

# ---------- List all roles ----------
@router.get("/", response_model=List[RoleResponse])
async def list_roles(
    filters: RoleListFilters = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Roles:read"])
):
    """
    List all roles with optional filtering.
    
    Retrieves a list of all admin roles in the system with their associated
    permissions. Used to view role hierarchy and permission assignments.
    Supports filtering and search across role names.
    
    Security:
        - Requires valid JWT access token
        - Scope: Roles:read
        - Restricted to admin/operations team
    
    Query Parameters (Filters):
        - search (str, optional): Search by role name (LIKE pattern)
        - limit (int, optional): Rows per page (default: 50, 0 = all)
        - offset (int, optional): Pagination offset (default: 0)
    
    Returns:
        List[RoleResponse]: Array of role objects, each containing:
            - role_id (int): Unique role identifier
            - role_name (str): Role name (e.g., "super-admin", "support-lead")
            - permissions (list): Associated permissions with operations:
                - permission_id (int): Unique identifier
                - resource (str): Resource name (Users, Plans, Backup, etc.)
                - read (bool): Read permission allowed
                - write (bool): Write/create permission allowed
                - delete (bool): Delete permission allowed
                - edit (bool): Edit permission allowed
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Roles:read scope
        HTTPException(400): Invalid filter parameters
    
    Example:
        Request:
            GET /roles/?search=admin&limit=20
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            [
                {
                    "role_id": 1,
                    "role_name": "super-admin",
                    "permissions": [
                        {
                            "permission_id": 1,
                            "resource": "Users",
                            "read": true,
                            "write": true,
                            "delete": true,
                            "edit": true
                        },
                        {
                            "permission_id": 2,
                            "resource": "Plans",
                            "read": true,
                            "write": true,
                            "delete": true,
                            "edit": true
                        }
                    ]
                }
            ]
    """
    roles = await crud_roles.get_all_roles(db, filters)
    return [
        {
            "role_id": role.role_id,
            "role_name": role.role_name,
            "permissions": [
                {
                    "permission_id": rp.permission.permission_id,
                    "resource": rp.permission.resource,
                    "read": rp.permission.read,
                    "write": rp.permission.write,
                    "delete": rp.permission.delete,
                    "edit": rp.permission.edit,
                }
                for rp in role.role_permissions
            ],
        }
        for role in roles
    ]


# ---------- Get a single role ----------
@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int, db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Roles:read"])
):
    """
    Retrieve details of a specific role.
    
    Fetch complete role information including all associated permissions and
    their specific operations (read, write, edit, delete). Used to understand
    what capabilities a particular role has.
    
    Security:
        - Requires valid JWT access token
        - Scope: Roles:read
        - Restricted to admin/operations team
    
    Path Parameters:
        - role_id (int): ID of role to retrieve (must exist)
    
    Returns:
        RoleResponse: Role object with:
            - role_id (int): Unique identifier
            - role_name (str): Role name
            - permissions (list): All associated permissions with details:
                - permission_id (int): Permission identifier
                - resource (str): Resource this permission applies to
                - read (bool): Can read resource
                - write (bool): Can create/write resource
                - delete (bool): Can delete resource
                - edit (bool): Can edit resource
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Roles:read scope
        HTTPException(404): Role not found
    
    Example:
        Request:
            GET /roles/2
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            {
                "role_id": 2,
                "role_name": "support-lead",
                "permissions": [
                    {
                        "permission_id": 5,
                        "resource": "Users",
                        "read": true,
                        "write": false,
                        "delete": false,
                        "edit": true
                    },
                    {
                        "permission_id": 6,
                        "resource": "Recharge",
                        "read": true,
                        "write": false,
                        "delete": false,
                        "edit": false
                    }
                ]
            }
    """
    role = await crud_roles.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return {
            "role_id": role.role_id,
            "role_name": role.role_name,
            "permissions": [
                {
                    "permission_id": rp.permission.permission_id,
                    "resource": rp.permission.resource,
                    "read": rp.permission.read,
                    "write": rp.permission.write,
                    "delete": rp.permission.delete,
                    "edit": rp.permission.edit,
                }
                for rp in role.role_permissions
            ],
        }
        

# ---------- Create role ----------
@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate, db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Roles:write"])     
):
    """
    Create a new role with specified permissions.
    
    Adds a new admin role to the system with a specific set of permissions.
    New roles can then be assigned to admin users. Role names must be unique.
    
    Security:
        - Requires valid JWT access token
        - Scope: Roles:write
        - Only super-admin can create roles
    
    Request Body:
        RoleCreate (JSON):
            - role_name (str): Unique role name (e.g., "content-manager")
            - permission_ids (list): Array of permission IDs to assign
                - Each ID must correspond to existing permission
    
    Returns:
        RoleResponse: Created role with:
            - role_id (int): Assigned ID
            - role_name (str): Role name
            - permissions (list): All assigned permissions with full details
    
    Raises:
        HTTPException(400): Invalid data or validation error
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Roles:write scope
        HTTPException(409): Role name already exists
        HTTPException(422): One or more permission IDs not found
    
    Example:
        Request:
            POST /roles/
            Headers: Authorization: Bearer <jwt_token>
            Body:
            {
                "role_name": "content-manager",
                "permission_ids": [20, 21, 22]
            }
        
        Response (201 Created):
            {
                "role_id": 5,
                "role_name": "content-manager",
                "permissions": [
                    {
                        "permission_id": 20,
                        "resource": "Content",
                        "read": true,
                        "write": true,
                        "delete": true,
                        "edit": true
                    },
                    {
                        "permission_id": 21,
                        "resource": "Analytics",
                        "read": true,
                        "write": false,
                        "delete": false,
                        "edit": false
                    }
                ]
            }
    """
    role = await crud_roles.create_role(db, role_data.role_name, role_data.permission_ids)
    return {
            "role_id": role.role_id,
            "role_name": role.role_name,
            "permissions": [
                {
                    "permission_id": rp.permission_id,
                    "resource": rp.permission.resource,
                    "read": rp.permission.read,
                    "write": rp.permission.write,
                    "delete": rp.permission.delete,
                    "edit": rp.permission.edit,
                }
                for rp in role.role_permissions
            ],
        }

# ---------- Update role ----------
@router.put("/{role_id}", response_model=RoleResponse)
async def update_role_endpoint(
    role_id: int,
    role_data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Roles:edit"])
):
    """
    Update an existing role's name and permissions.
    
    Modifies role details including name and assigned permissions. Changes
    take effect immediately for all users with this role. Cannot rename to
    an existing role name.
    
    Security:
        - Requires valid JWT access token
        - Scope: Roles:edit
        - Only super-admin can edit roles
    
    Path Parameters:
        - role_id (int): ID of role to update (must exist)
    
    Request Body:
        RoleUpdate (JSON):
            - role_name (str, optional): New role name (must be unique)
            - permission_ids (list, optional): New set of permission IDs to assign
    
    Returns:
        RoleResponse: Updated role with:
            - role_id (int): Role ID
            - role_name (str): Updated name
            - permissions (list): Updated permissions list
    
    Raises:
        HTTPException(400): Invalid update data
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Roles:edit scope
        HTTPException(404): Role not found
        HTTPException(409): New role name already in use
        HTTPException(422): Permission ID not found
    
    Example:
        Request:
            PUT /roles/5
            Headers: Authorization: Bearer <jwt_token>
            Body:
            {
                "role_name": "content-editor",
                "permission_ids": [20, 21]
            }
        
        Response (200 OK):
            {
                "role_id": 5,
                "role_name": "content-editor",
                "permissions": [
                    {
                        "permission_id": 20,
                        "resource": "Content",
                        "read": true,
                        "write": true,
                        "delete": false,
                        "edit": true
                    }
                ]
            }
    """
    role = await crud_roles.update_role(
        db, role_id, role_data.role_name, role_data.permission_ids
    )
    return {
        "role_id": role.role_id,
        "role_name": role.role_name,
        "permissions": [
            {
                "permission_id": rp.permission.permission_id,
                "resource": rp.permission.resource,
                "read": rp.permission.read,
                "write": rp.permission.write,
                "delete": rp.permission.delete,
                "edit": rp.permission.edit,
            }
            for rp in role.role_permissions
        ],
    }

# ---------- Delete role ----------
@router.delete("/{role_id}")
async def delete_role(
    role_id: int, db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Roles:delete"])
):
    """
    Delete a role from the system.
    
    Removes a role permanently. Cannot delete roles that are still assigned to
    admin users. Reassign all admins with this role first. This action is
    logged for audit purposes.
    
    Security:
        - Requires valid JWT access token
        - Scope: Roles:delete
        - Only super-admin can delete roles
    
    Path Parameters:
        - role_id (int): ID of role to delete (must exist and have no users)
    
    Returns:
        dict: Deletion confirmation:
            {
                "message": "Role deleted successfully",
                "role_id": <int>,
                "deleted_at": <datetime>
            }
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Roles:delete scope
        HTTPException(404): Role not found
        HTTPException(409): Role still assigned to admin users
    
    Example:
        Request:
            DELETE /roles/5
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            {
                "message": "Role deleted successfully",
                "role_id": 5,
                "deleted_at": "2024-01-20T10:30:00Z"
            }
    """
    return await crud_roles.delete_role(db, role_id)

# ---------- List all permissions ----------
@router.get("/permissions/all", response_model=List[PermissionBase])
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Roles:read"])
):
    """
    List all available permissions in the system.
    
    Retrieves a complete list of all system permissions that can be assigned
    to roles. Used when creating or editing roles to see what permissions
    are available for assignment.
    
    Security:
        - Requires valid JWT access token
        - Scope: Roles:read
        - Restricted to admin/operations team
    
    Returns:
        List[PermissionBase]: Array of permission objects:
            - permission_id (int): Unique identifier
            - resource (str): Resource this permission governs (Users, Plans, etc.)
            - read (bool): Read access granted by this permission
            - write (bool): Write/create access granted
            - delete (bool): Delete access granted
            - edit (bool): Edit access granted
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Roles:read scope
    
    Example:
        Request:
            GET /roles/permissions/all
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            [
                {
                    "permission_id": 1,
                    "resource": "Users",
                    "read": true,
                    "write": true,
                    "delete": true,
                    "edit": true
                },
                {
                    "permission_id": 2,
                    "resource": "Plans",
                    "read": true,
                    "write": true,
                    "delete": true,
                    "edit": true
                },
                {
                    "permission_id": 3,
                    "resource": "Backup",
                    "read": true,
                    "write": true,
                    "delete": false,
                    "edit": true
                }
            ]
    """
    permissions = await crud_roles.get_all_permissions(db)
    return permissions
