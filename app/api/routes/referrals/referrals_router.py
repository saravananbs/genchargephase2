# app/api/v1/endpoints/referral.py
from fastapi import APIRouter, Depends, Query, Security
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal

from ....core.database import get_db
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes
from ....models.users import User
from ....schemas.referrals import (
    PaginatedReferralReward,
    ReferralRewardStatus,
)
from app.services.referral import get_my_referral_history, get_all_referral_history

router = APIRouter()


@router.get("/me", response_model=PaginatedReferralReward)
async def my_referral_history(
    page: int = Query(0, ge=0),
    size: int = Query(0, ge=0, le=100),
    status: ReferralRewardStatus | None = None,
    sort: Literal[
        "created_at_desc", "created_at_asc",
        "reward_amount_desc", "reward_amount_asc"
    ] = "created_at_desc",
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["User"])
):
    """
    View personal referral history and rewards.
    
    Retrieves all referral-related rewards and earnings for the current user,
    including earnings from referring others and rewards received from being
    referred. Shows referral activity status and financial details.
    
    Security:
        - Requires valid JWT access token
        - Scope: User
        - Users can only view their own referral history
    
    Query Parameters:
        - page (int, optional): Page number (default: 1, minimum: 1)
        - size (int, optional): Records per page (default: 20, max: 100)
        - status (str, optional): Filter by reward status (pending, credited, disputed)
        - sort (str, optional): Sort order (default: created_at_desc):
            - created_at_desc: Newest first
            - created_at_asc: Oldest first
            - reward_amount_desc: Highest earnings first
            - reward_amount_asc: Lowest earnings first
    
    Returns:
        PaginatedReferralReward:
            - items (list): Referral reward objects:
                - referral_id (str): Unique identifier
                - referrer_user_id (int): User who made referral
                - referred_user_id (int): User who was referred
                - reward_amount (float): Reward given
                - reward_type (str): Type of reward (credit, discount, cashback)
                - status (str): Reward status (pending, credited, disputed)
                - created_at (datetime): When referral was initiated
                - credited_at (datetime, optional): When reward was credited
            - total (int): Total referral rewards
            - page (int): Current page
            - size (int): Records per page
            - pages (int): Total pages
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing User scope
        HTTPException(400): Invalid pagination parameters
    
    Example:
        Request:
            GET /referrals/me?page=1&size=20&status=credited&sort=reward_amount_desc
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            {
                "items": [
                    {
                        "referral_id": "ref_001",
                        "referrer_user_id": 42,
                        "referred_user_id": 123,
                        "reward_amount": 50.00,
                        "reward_type": "credit",
                        "status": "credited",
                        "created_at": "2024-01-15T10:00:00Z",
                        "credited_at": "2024-01-16T10:00:00Z"
                    },
                    {
                        "referral_id": "ref_002",
                        "referrer_user_id": 42,
                        "referred_user_id": 124,
                        "reward_amount": 35.00,
                        "reward_type": "credit",
                        "status": "credited",
                        "created_at": "2024-01-10T10:00:00Z",
                        "credited_at": "2024-01-11T10:00:00Z"
                    }
                ],
                "total": 5,
                "page": 1,
                "size": 20,
                "pages": 1
            }
    """
    return await get_my_referral_history(
        db,
        current_user_id=current_user.user_id,
        page=page,
        size=size,
        status=status,
        sort=sort,
    )


@router.get("/admin/all", response_model=PaginatedReferralReward)
async def admin_referral_history(
    page: int = Query(0, ge=0),
    size: int = Query(0, ge=0, le=100),
    status: ReferralRewardStatus | None = None,
    sort: Literal[
        "created_at_desc", "created_at_asc",
        "reward_amount_desc", "reward_amount_asc"
    ] = "created_at_desc",
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Referral:read"])
):
    """
    View all referral rewards in the system (Admin view).
    
    Retrieves system-wide referral rewards and earnings across all users.
    Used by admins to monitor referral program performance, detect fraud,
    verify reward calculations, and analyze referral program metrics.
    
    Security:
        - Requires valid JWT access token
        - Scope: Referral:read
        - Restricted to admin/analytics team
    
    Query Parameters:
        - page (int, optional): Page number (default: 1, minimum: 1)
        - size (int, optional): Records per page (default: 20, max: 100)
        - status (str, optional): Filter by reward status (pending, credited, disputed)
        - sort (str, optional): Sort order (default: created_at_desc):
            - created_at_desc: Most recent first
            - created_at_asc: Oldest first
            - reward_amount_desc: Highest rewards first
            - reward_amount_asc: Lowest rewards first
    
    Returns:
        PaginatedReferralReward:
            - items (list): Referral reward objects across all users:
                - referral_id (str): Unique identifier
                - referrer_user_id (int): User who made referral
                - referred_user_id (int): User who was referred
                - reward_amount (float): Reward given
                - reward_type (str): Type of reward (credit, discount, cashback)
                - status (str): Reward status (pending, credited, disputed)
                - created_at (datetime): When referral was initiated
                - credited_at (datetime, optional): When reward was credited
            - total (int): Total referrals in system
            - page (int): Current page
            - size (int): Records per page
            - pages (int): Total pages
    
    Raises:
        HTTPException(401): User not authenticated
        HTTPException(403): Missing Referral:read scope
        HTTPException(400): Invalid pagination parameters
    
    Example:
        Request:
            GET /referrals/admin/all?page=1&size=50&status=pending&sort=created_at_desc
            Headers: Authorization: Bearer <jwt_token>
        
        Response (200 OK):
            {
                "items": [
                    {
                        "referral_id": "ref_500",
                        "referrer_user_id": 50,
                        "referred_user_id": 200,
                        "reward_amount": 75.00,
                        "reward_type": "credit",
                        "status": "pending",
                        "created_at": "2024-01-20T10:00:00Z"
                    },
                    {
                        "referral_id": "ref_499",
                        "referrer_user_id": 42,
                        "referred_user_id": 123,
                        "reward_amount": 50.00,
                        "reward_type": "credit",
                        "status": "credited",
                        "created_at": "2024-01-15T10:00:00Z",
                        "credited_at": "2024-01-16T10:00:00Z"
                    }
                ],
                "total": 856,
                "page": 1,
                "size": 50,
                "pages": 18
            }
    """
    return await get_all_referral_history(
        db, page=page, size=size, status=status, sort=sort
    )