from fastapi import APIRouter, Depends, HTTPException, status, Query, Security
from typing import List, Optional, Literal
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.document_db import get_mongo_db
from ....models.users import User
from ....core.database import get_db
from ....dependencies.auth import get_current_user
from ....dependencies.permissions import require_scopes
from ....schemas.recharge import (
    RechargeRequest,
    WalletTopupRequest,
    TransactionOut,
    CurrentActivePlanOut,
    CurrentPlanListResponse,
    TransactionListResponse,
    CurrentPlanFilterParams,
    TransactionFilterParams,
    UserCurrentPlanFilterParams,
    UserTransactionFilterParams
)
from ....models.current_active_plans import CurrentPlanStatus
from ....models.transactions import TransactionCategory, TransactionType, TransactionStatus
from ....services.recharge import (
    subscribe_plan,
    wallet_topup,
    get_my_active_plans,
    get_my_transactions,
    admin_list_active_plans,
    admin_list_transactions,
)

router = APIRouter()


# ====================== USER ENDPOINTS ======================
@router.post("/subscribe", response_model=TransactionOut)
async def subscribe(
    request: RechargeRequest,
    db=Depends(get_db),
    mongo_db = Depends(get_mongo_db),
    current_user=Depends(get_current_user),
    _=Security(require_scopes, scopes=["User"]),
):
    """
    Subscribe to a plan or apply an offer to current user.
    
    User endpoint to purchase a plan subscription or apply promotional offers to their account.
    Supports recharging with plans and adding benefits via offers. Transaction is created with
    wallet deduction if applicable. Returns transaction details confirming the operation.
    
    Security:
        - Requires valid JWT access token
        - Scope: User (any authenticated user)
        - User can only subscribe for themselves
    
    Request Body (RechargeRequest):
        - plan_id (int, optional): ID of plan to subscribe to
        - offer_id (int, optional): ID of offer to apply
        - payment_method (str, optional): 'wallet', 'credit_card', 'upi', etc
        - amount (Decimal, optional): Transaction amount
    
    Returns:
        TransactionOut: Complete transaction object with subscription details.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing User scope.
        HTTPException(400): If insufficient wallet balance, plan expired, or offer invalid.
        HTTPException(404): If plan or offer not found.
    
    Example:
        Request:
        ```json
        {
            "plan_id": 5,
            "offer_id": 2,
            "payment_method": "wallet"
        }
        ```
        
        Response:
        ```json
        {
            "transaction_id": "TXN001",
            "user_id": 1,
            "amount": 199.00,
            "plan_id": 5,
            "offer_id": 2,
            "status": "success",
            "created_at": "2024-01-20T10:15:00Z"
        }
        ```
    """
    try:
        return await subscribe_plan(db=db, mongo_db=mongo_db, request=request, current_user=current_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/wallet/topup", response_model=TransactionOut)
async def topup(
    request: WalletTopupRequest,
    db=Depends(get_db),
    mongo_db = Depends(get_mongo_db),
    current_user=Depends(get_current_user),
    _=Security(require_scopes, scopes=["User"]),
):
    """
    Add funds to user wallet via payment.
    
    User endpoint to top up their wallet with additional funds. Supports multiple payment methods
    and creates a transaction record. Topped-up wallet funds can be used for plan subscriptions,
    offer purchases, or other paid services.
    
    Security:
        - Requires valid JWT access token
        - Scope: User
        - User can only top up their own wallet
    
    Request Body (WalletTopupRequest):
        - amount (Decimal): Amount to add to wallet (must be > 0, typically 10-10000)
        - payment_method (str): 'credit_card', 'debit_card', 'upi', 'net_banking', 'wallet'
        - description (str, optional): Transaction description/memo
    
    Returns:
        TransactionOut: Transaction object confirming wallet top-up with new balance.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing User scope.
        HTTPException(400): If amount invalid or payment method not supported.
        HTTPException(402): If payment processing failed.
    
    Example:
        Request:
        ```json
        {
            "amount": 500.00,
            "payment_method": "upi"
        }
        ```
        
        Response:
        ```json
        {
            "transaction_id": "TOPUP001",
            "user_id": 1,
            "amount": 500.00,
            "transaction_type": "wallet_topup",
            "payment_method": "upi",
            "status": "success",
            "new_wallet_balance": 1750.50,
            "created_at": "2024-01-20T10:20:00Z"
        }
        ```
    """
    try:
        return await wallet_topup(db, mongo_db, request, current_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my/plans", response_model=CurrentPlanListResponse)
async def my_plans(
    filters: UserCurrentPlanFilterParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ = Security(require_scopes, scopes=["User"]),
):
    """
    Retrieve current user's active plan subscriptions.
    
    User endpoint to view all active and upcoming plan subscriptions. Shows subscription status,
    validity periods, benefits, and renewal dates. Useful for users to track their current plans
    and monitor expiration.
    
    Security:
        - Requires valid JWT access token
        - Scope: User
        - Returns only current user's plans
    
    Query Parameters (UserCurrentPlanFilterParams):
        - status (str, optional): 'active', 'expired', 'upcoming'
        - plan_id (int, optional): Filter by specific plan
        - valid_from_date (datetime, optional): Plans valid after this date
        - valid_to_date (datetime, optional): Plans valid before this date
        - sort_by (str): 'valid_from' or 'valid_to' (default: 'valid_to')
        - sort_order (str): 'asc' or 'desc' (default: 'desc')
        - page (int): Page number (default: 1)
        - size (int): Records per page (0 = all records, default: 10)
    
    Returns:
        CurrentPlanListResponse: Paginated list of user's active plans with details.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing User scope.
    
    Example:
        Request:
        ```
        GET /recharge/my/plans?status=active&sort_by=valid_to&sort_order=desc
        Authorization: Bearer <token>
        ```
        
        Response:
        ```json
        {
            "total": 2,
            "page": 1,
            "limit": 10,
            "items": [
                {
                    "plan_id": 5,
                    "plan_name": "Premium 199",
                    "validity_days": 30,
                    "valid_from": "2024-01-01T00:00:00Z",
                    "valid_to": "2024-02-01T00:00:00Z",
                    "status": "active"
                }
            ]
        }
        ```
    """
    res = CurrentPlanFilterParams(**filters.model_dump())
    res.phone_number = current_user.phone_number
    return await admin_list_active_plans(db, res)

@router.get("/my/transactions", response_model=TransactionListResponse)
async def my_transactions(
    f: UserTransactionFilterParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ = Security(require_scopes, scopes=["User"]),
):
    """
    Retrieve current user's transaction history.
    
    User endpoint to view all their transactions including plan subscriptions, wallet top-ups,
    offer purchases, refunds, and other financial activities. Supports advanced filtering and
    pagination for easy history browsing.
    
    Security:
        - Requires valid JWT access token
        - Scope: User
        - Returns only current user's transactions
    
    Query Parameters (UserTransactionFilterParams):
        - category (str, optional): 'recharge', 'wallet', 'offer', 'refund', etc
        - txn_type (str, optional): 'credit', 'debit'
        - status (str, optional): 'success', 'pending', 'failed'
        - payment_method (str, optional): 'wallet', 'credit_card', 'upi', etc
        - amount_min (Decimal, optional): Minimum transaction amount
        - amount_max (Decimal, optional): Maximum transaction amount
        - created_from (datetime, optional): Transactions after this date
        - created_to (datetime, optional): Transactions before this date
        - sort_by (str): 'created_at' or 'amount' (default: 'created_at')
        - sort_order (str): 'asc' or 'desc' (default: 'desc')
        - page (int): Page number (default: 1)
        - size (int): Records per page (0 = all, default: 10, max: 10000)
    
    Returns:
        TransactionListResponse: Paginated list of transactions with complete details.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing User scope.
    
    Example:
        Request:
        ```
        GET /recharge/my/transactions?status=success&category=recharge&page=1&size=20
        Authorization: Bearer <token>
        ```
        
        Response:
        ```json
        {
            "total": 25,
            "page": 1,
            "limit": 20,
            "items": [
                {
                    "transaction_id": "TXN12345",
                    "user_id": 1,
                    "amount": 199.00,
                    "category": "recharge",
                    "type": "debit",
                    "status": "success",
                    "payment_method": "wallet",
                    "created_at": "2024-01-20T10:15:00Z"
                }
            ]
        }
        ```
    
    Note:
        - Set `size=0` to retrieve ALL matching transactions without pagination
        - All enum fields (category, type, status, payment_method) appear as dropdowns in Swagger
        - Date fields include date picker in Swagger UI
    """
    res = TransactionFilterParams(**f.model_dump())
    res.from_phone_number = current_user.phone_number
    return await admin_list_transactions(db, res)


# ====================== ADMIN ENDPOINTS ======================
@router.get("/admin/active-plans", response_model=CurrentPlanListResponse)
async def admin_active_plans(
    filters: CurrentPlanFilterParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Security(require_scopes, scopes=["Recharge:read"]),
):
    """
    Retrieve all active plan subscriptions across all users.
    
    Admin endpoint to view system-wide active plan subscriptions. Supports extensive filtering
    by user phone, plan ID, validity dates, and status. Useful for analyzing subscription
    patterns and managing active plans.
    
    Security:
        - Requires valid JWT access token
        - Scope: Recharge:read
        - Admin-only endpoint
    
    Query Parameters (CurrentPlanFilterParams):
        - phone_number (str, optional): Filter by user phone (supports LIKE pattern)
        - plan_id (int, optional): Filter by specific plan
        - plan_type (str, optional): Filter by plan type (voice, data, voice_data, etc)
        - status (str, optional): 'active', 'expired', 'upcoming'
        - valid_from_date (datetime, optional): Plans valid from after this date
        - valid_to_date (datetime, optional): Plans valid until before this date
        - user_type (str, optional): 'prepaid', 'postpaid'
        - is_active (bool, optional): Filter by user active status
        - sort_by (str): 'valid_from' or 'valid_to' (default: 'valid_to')
        - sort_order (str): 'asc' or 'desc' (default: 'desc')
        - page (int): Page number (default: 1)
        - size (int): Records per page (0 = all, default: 10)
    
    Returns:
        CurrentPlanListResponse: Paginated list of active plans with user and plan details.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing Recharge:read scope.
    
    Example:
        Request:
        ```
        GET /recharge/admin/active-plans?status=active&plan_type=voice_data&page=1&size=50
        Authorization: Bearer <admin_token>
        ```
        
        Response:
        ```json
        {
            "total": 1250,
            "page": 1,
            "limit": 50,
            "items": [
                {
                    "plan_id": 5,
                    "plan_name": "Premium 199",
                    "user_phone": "+919876543210",
                    "validity_days": 30,
                    "valid_from": "2024-01-01T00:00:00Z",
                    "valid_to": "2024-02-01T00:00:00Z",
                    "status": "active"
                }
            ]
        }
        ```
    """
    return await admin_list_active_plans(db, filters)

@router.get("/admin/transactions", response_model=TransactionListResponse)
async def admin_transactions(
    f: TransactionFilterParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Security(require_scopes, scopes=["Recharge:read"]),
):
    """
    Retrieve all transactions across the system with advanced filtering.
    
    Admin endpoint for comprehensive transaction reporting and analysis. Supports 23+ filter
    options including user phone, transaction type, amount ranges, dates, status, payment method,
    and more. Provides full visibility into all financial activities.
    
    Security:
        - Requires valid JWT access token
        - Scope: Recharge:read
        - Admin-only endpoint
    
    Query Parameters (TransactionFilterParams):
        - from_phone_number (str, optional): User phone (LIKE search, e.g., '%9876%')
        - category (str, optional): 'recharge', 'wallet_topup', 'offer', 'refund', 'bonus'
        - txn_type (str, optional): 'credit', 'debit'
        - service_type (str, optional): 'sms', 'call', 'data', 'plan', 'ott'
        - source (str, optional): 'web', 'mobile_app', 'api', 'admin'
        - status (str, optional): 'success', 'pending', 'failed', 'cancelled'
        - payment_method (str, optional): 'wallet', 'credit_card', 'debit_card', 'upi', 'net_banking'
        - amount_min (Decimal, optional): Minimum transaction amount (> 0)
        - amount_max (Decimal, optional): Maximum transaction amount (< 999999)
        - created_from (datetime, optional): Transactions after this date
        - created_to (datetime, optional): Transactions before this date
        - user_type (str, optional): 'prepaid', 'postpaid'
        - sort_by (str): 'created_at' or 'amount' (default: 'created_at')
        - sort_order (str): 'asc' or 'desc' (default: 'desc')
        - page (int): Page number (default: 1)
        - size (int): Records per page (0 = all, default: 10, max: 10000 for performance)
    
    Returns:
        TransactionListResponse: Paginated list of transactions with complete details.
        
    Raises:
        HTTPException(401): If not authenticated.
        HTTPException(403): If missing Recharge:read scope.
    
    Example:
        Request:
        ```
        GET /recharge/admin/transactions?status=success&category=recharge&amount_min=100&amount_max=500&page=1&size=100
        Authorization: Bearer <admin_token>
        ```
        
        Response:
        ```json
        {
            "total": 5432,
            "page": 1,
            "limit": 100,
            "items": [
                {
                    "transaction_id": "TXN12345",
                    "user_phone": "+919876543210",
                    "amount": 199.00,
                    "category": "recharge",
                    "type": "debit",
                    "status": "success",
                    "payment_method": "wallet",
                    "service_type": "plan",
                    "source": "mobile_app",
                    "created_at": "2024-01-20T10:15:00Z"
                }
            ]
        }
        ```
    
    Notes:
        - Set `size=0` to return ALL matching transactions (be careful with large result sets)
        - All enum fields appear as dropdowns in Swagger UI
        - Date fields include date picker in Swagger
        - Phone search supports LIKE patterns (% wildcards)
        - Maximum 10,000 records per page for performance
    """
    return await admin_list_transactions(db, f)