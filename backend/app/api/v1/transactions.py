"""
Transaction CRUD Endpoints

Handles all transaction-related operations including creation,
retrieval, updates, deletion, and bulk operations.
"""

import logging
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import ActiveUser, DatabaseSession
from app.models.transaction import TransactionSource, TransactionType
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.transaction import (
    TransactionBulkCreateRequest,
    TransactionBulkCreateResponse,
    TransactionCreateRequest,
    TransactionDetailResponse,
    TransactionFilterParams,
    TransactionResponse,
    TransactionSummary,
    TransactionUpdateRequest,
)
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Transactions"])


@router.get(
    "",
    response_model=PaginatedResponse[TransactionResponse],
    summary="List transactions",
    description="Get paginated list of transactions with optional filters.",
)
async def list_transactions(
    current_user: ActiveUser,
    db: DatabaseSession,
    # Pagination
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    # Filters
    start_date: Optional[date] = Query(default=None, description="Filter from date"),
    end_date: Optional[date] = Query(default=None, description="Filter to date"),
    min_amount: Optional[float] = Query(default=None, ge=0, description="Minimum amount"),
    max_amount: Optional[float] = Query(default=None, ge=0, description="Maximum amount"),
    transaction_type: Optional[TransactionType] = Query(default=None),
    category_id: Optional[UUID] = Query(default=None),
    source: Optional[TransactionSource] = Query(default=None),
    is_recurring: Optional[bool] = Query(default=None),
    merchant_name: Optional[str] = Query(default=None, max_length=255),
    search: Optional[str] = Query(default=None, max_length=100),
    sort_by: str = Query(default="transaction_date", pattern="^(transaction_date|amount|created_at)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> PaginatedResponse[TransactionResponse]:
    """
    List transactions with pagination and filters.

    Supports filtering by:
    - Date range (start_date, end_date)
    - Amount range (min_amount, max_amount)
    - Transaction type (CREDIT/DEBIT)
    - Category
    - Source (MANUAL/PDF/CSV/EXCEL)
    - Recurring status
    - Merchant name
    - Search text
    """
    filters = TransactionFilterParams(
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        transaction_type=transaction_type,
        category_id=category_id,
        source=source,
        is_recurring=is_recurring,
        merchant_name=merchant_name,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    service = TransactionService(db)
    transactions, total = await service.list_transactions(
        user_id=current_user.id,
        filters=filters,
        page=page,
        page_size=page_size,
    )

    # Convert to response schema
    items = [service._to_response(txn) for txn in transactions]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create transaction",
    description="Create a new transaction.",
)
async def create_transaction(
    data: TransactionCreateRequest,
    current_user: ActiveUser,
    db: DatabaseSession,
) -> TransactionResponse:
    """
    Create a single transaction.

    - **amount**: Transaction amount (positive)
    - **transaction_type**: CREDIT (income) or DEBIT (expense)
    - **category_id**: Optional category UUID
    - **transaction_date**: Date and time of transaction
    - **merchant_name**: Optional merchant name
    - **description**: Optional description
    """
    service = TransactionService(db)
    transaction = await service.create_transaction(
        user_id=current_user.id,
        data=data,
        source=TransactionSource.MANUAL,
    )
    return service._to_response(transaction)


@router.post(
    "/bulk",
    response_model=TransactionBulkCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create transactions",
    description="Create multiple transactions at once.",
)
async def bulk_create_transactions(
    data: TransactionBulkCreateRequest,
    current_user: ActiveUser,
    db: DatabaseSession,
) -> TransactionBulkCreateResponse:
    """
    Bulk create transactions from parsed data.

    - **transactions**: List of transactions to create (max 500)
    - **source**: Source of transactions (MANUAL/PDF/CSV/EXCEL)
    - **upload_batch_id**: Optional batch ID from file upload
    """
    service = TransactionService(db)
    return await service.bulk_create_transactions(
        user_id=current_user.id,
        data=data,
    )


@router.get(
    "/summary",
    response_model=TransactionSummary,
    summary="Get transaction summary",
    description="Get summary statistics for transactions.",
)
async def get_transaction_summary(
    current_user: ActiveUser,
    db: DatabaseSession,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
) -> TransactionSummary:
    """
    Get summary statistics including:
    - Total income and expenses
    - Net amount
    - Transaction count
    - Average transaction amount
    - Largest income/expense
    """
    service = TransactionService(db)
    return await service.get_summary(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/search",
    response_model=list[TransactionResponse],
    summary="Search transactions",
    description="Full-text search across transactions.",
)
async def search_transactions(
    current_user: ActiveUser,
    db: DatabaseSession,
    query: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[TransactionResponse]:
    """
    Search transactions by:
    - Merchant name
    - Description
    - Notes
    """
    service = TransactionService(db)
    transactions = await service.search_transactions(
        user_id=current_user.id,
        query=query,
        limit=limit,
    )
    return [service._to_response(txn) for txn in transactions]


@router.get(
    "/{transaction_id}",
    response_model=TransactionDetailResponse,
    summary="Get transaction",
    description="Get a single transaction by ID.",
)
async def get_transaction(
    transaction_id: UUID,
    current_user: ActiveUser,
    db: DatabaseSession,
) -> TransactionDetailResponse:
    """
    Get detailed information about a specific transaction.
    """
    service = TransactionService(db)
    transaction = await service.get_transaction(
        transaction_id=transaction_id,
        user_id=current_user.id,
    )

    response = service._to_response(transaction)
    return TransactionDetailResponse(
        **response.model_dump(),
        upload_batch_id=transaction.upload_batch_id,
    )


@router.put(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Update transaction",
    description="Update an existing transaction.",
)
async def update_transaction(
    transaction_id: UUID,
    data: TransactionUpdateRequest,
    current_user: ActiveUser,
    db: DatabaseSession,
) -> TransactionResponse:
    """
    Update a transaction's details.
    Only provided fields will be updated.
    """
    service = TransactionService(db)
    transaction = await service.update_transaction(
        transaction_id=transaction_id,
        user_id=current_user.id,
        data=data,
    )
    return service._to_response(transaction)


@router.delete(
    "/{transaction_id}",
    response_model=MessageResponse,
    summary="Delete transaction",
    description="Soft delete a transaction.",
)
async def delete_transaction(
    transaction_id: UUID,
    current_user: ActiveUser,
    db: DatabaseSession,
    hard_delete: bool = Query(default=False, description="Permanently delete"),
) -> MessageResponse:
    """
    Delete a transaction.

    By default, performs a soft delete (can be restored).
    Set hard_delete=true to permanently remove.
    """
    service = TransactionService(db)
    await service.delete_transaction(
        transaction_id=transaction_id,
        user_id=current_user.id,
        hard_delete=hard_delete,
    )

    return MessageResponse(
        message="Transaction deleted successfully",
        success=True,
    )
