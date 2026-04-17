"""
Transaction Pydantic schemas for request/response validation.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.transaction import TransactionSource, TransactionType
from app.schemas.common import BaseSchema, TimestampMixin


# ====================
# Request Schemas
# ====================


class TransactionCreateRequest(BaseModel):
    """Schema for creating a single transaction."""

    amount: Decimal = Field(
        ...,
        gt=0,
        description="Transaction amount (positive value)",
    )
    transaction_type: TransactionType = Field(..., description="CREDIT or DEBIT")
    category_id: UUID | None = Field(default=None, description="Category ID")
    merchant_name: str | None = Field(default=None, max_length=255)
    merchant_category: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    transaction_date: datetime = Field(..., description="Date of transaction")
    bank_name: str | None = Field(default=None, max_length=100)
    account_last_4: str | None = Field(default=None, max_length=4)
    tags: list[str] | None = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=1000)
    is_recurring: bool = Field(default=False)

    @field_validator("account_last_4")
    @classmethod
    def validate_account_last_4(cls, v: str | None) -> str | None:
        """Validate account last 4 digits."""
        if v is not None and (not v.isdigit() or len(v) != 4):
            raise ValueError("Account last 4 must be exactly 4 digits")
        return v
    
    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate amount has at most 2 decimal places."""
        if v.as_tuple().exponent < -2:
            raise ValueError("Amount can have at most 2 decimal places")
        return round(v, 2)


class TransactionUpdateRequest(BaseModel):
    """Schema for updating a transaction."""

    amount: Decimal | None = Field(default=None, gt=0)
    transaction_type: TransactionType | None = None
    category_id: UUID | None = None
    merchant_name: str | None = None
    merchant_category: str | None = None
    description: str | None = None
    transaction_date: datetime | None = None
    tags: list[str] | None = None
    notes: str | None = None
    is_recurring: bool | None = None


class TransactionBulkCreateRequest(BaseModel):
    """Schema for bulk creating transactions."""

    transactions: list[TransactionCreateRequest] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="List of transactions to create",
    )
    source: TransactionSource = Field(
        default=TransactionSource.MANUAL,
        description="Source of the transactions",
    )
    upload_batch_id: UUID | None = Field(
        default=None,
        description="ID linking to upload batch",
    )


class TransactionFilterParams(BaseModel):
    """Schema for transaction filter parameters."""

    # Date filters
    start_date: date | None = Field(default=None, description="Filter from date")
    end_date: date | None = Field(default=None, description="Filter to date")

    # Amount filters
    min_amount: Decimal | None = Field(default=None, ge=0)
    max_amount: Decimal | None = Field(default=None, ge=0)

    # Type and category filters
    transaction_type: TransactionType | None = None
    category_id: UUID | None = None
    category_ids: list[UUID] | None = None

    # Source and status filters
    source: TransactionSource | None = None
    is_recurring: bool | None = None

    # Merchant filter
    merchant_name: str | None = None

    # Search
    search: str | None = Field(default=None, max_length=100)

    # Sorting
    sort_by: Literal["transaction_date", "amount", "created_at"] = "transaction_date"
    sort_order: Literal["asc", "desc"] = "desc"

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date | None, info) -> date | None:
        """Validate that end_date is after start_date."""
        if v is not None and "start_date" in info.data and info.data["start_date"]:
            if v < info.data["start_date"]:
                raise ValueError("end_date must be after start_date")
        return v


class TransactionSearchRequest(BaseModel):
    """Schema for full-text search request."""

    query: str = Field(..., min_length=1, max_length=100)
    limit: int = Field(default=20, ge=1, le=100)


# ====================
# Response Schemas
# ====================


class CategoryBrief(BaseSchema):
    """Brief category info for transaction response."""

    id: UUID
    name: str
    icon: str | None = None
    color: str | None = None


class TransactionResponse(BaseSchema, TimestampMixin):
    """Schema for transaction response."""

    id: UUID
    user_id: UUID
    amount: Decimal
    transaction_type: TransactionType
    category: CategoryBrief | None = None
    merchant_name: str | None = None
    merchant_category: str | None = None
    description: str | None = None
    transaction_date: datetime
    source: TransactionSource
    bank_name: str | None = None
    account_last_4: str | None = None
    confidence_score: float | None = None
    is_auto_categorized: bool = False
    is_recurring: bool = False
    recurring_pattern: str | None = None
    tags: list[str] = []
    notes: str | None = None


class TransactionDetailResponse(TransactionResponse):
    """Detailed transaction response with additional fields."""

    upload_batch_id: UUID | None = None


class TransactionBulkCreateResponse(BaseModel):
    """Response for bulk transaction creation."""

    created_count: int
    failed_count: int
    duplicate_count: int
    transactions: list[TransactionResponse]
    errors: list[dict] | None = None


class TransactionSummary(BaseModel):
    """Summary statistics for transactions."""

    total_income: Decimal
    total_expense: Decimal
    net_amount: Decimal
    transaction_count: int
    avg_transaction_amount: Decimal
    largest_expense: Decimal | None = None
    largest_income: Decimal | None = None


# Aliases for backwards compatibility
TransactionCreate = TransactionCreateRequest
TransactionUpdate = TransactionUpdateRequest
TransactionFilter = TransactionFilterParams
