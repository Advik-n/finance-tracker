"""
Upload Pydantic schemas for file upload handling.
"""

import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UploadStatus(str, enum.Enum):
    """Upload job status."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"


class FileType(str, enum.Enum):
    """Supported file types."""

    PDF = "PDF"
    CSV = "CSV"
    EXCEL = "EXCEL"
    IMAGE = "IMAGE"


# ====================
# Response Schemas
# ====================


class UploadInitResponse(BaseModel):
    """Response when upload is initiated."""

    job_id: UUID
    status: UploadStatus = UploadStatus.PENDING
    message: str = "File upload started"
    file_name: str
    file_type: FileType


class UploadStatusResponse(BaseModel):
    """Response for upload status check."""

    job_id: UUID
    status: UploadStatus
    progress: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    message: str | None = None

    # Results (when completed)
    transactions_found: int | None = None
    transactions_created: int | None = None
    duplicates_skipped: int | None = None
    errors: list[str] | None = None

    # Timing
    started_at: datetime | None = None
    completed_at: datetime | None = None


class UploadHistoryItem(BaseModel):
    """Single item in upload history."""

    job_id: UUID
    file_name: str
    file_type: FileType
    status: UploadStatus
    transactions_created: int = 0
    uploaded_at: datetime
    completed_at: datetime | None = None
    file_size_bytes: int | None = None


class UploadHistoryResponse(BaseModel):
    """Upload history response."""

    items: list[UploadHistoryItem]
    total: int


class ParsedTransaction(BaseModel):
    """Transaction parsed from file before confirmation."""

    temp_id: str
    amount: float
    transaction_type: str
    description: str | None = None
    merchant_name: str | None = None
    transaction_date: datetime
    suggested_category_id: UUID | None = None
    suggested_category_name: str | None = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    is_duplicate: bool = False
    raw_text: str | None = None


class ParsePreviewResponse(BaseModel):
    """Preview of parsed transactions before confirmation."""

    job_id: UUID
    file_name: str
    file_type: FileType
    transactions: list[ParsedTransaction]
    total_found: int
    duplicates_found: int
    parse_warnings: list[str] = []


class ConfirmUploadRequest(BaseModel):
    """Request to confirm and save parsed transactions."""

    job_id: UUID
    selected_transactions: list[str] = Field(
        ...,
        description="List of temp_ids to import",
    )
    category_overrides: dict[str, UUID] | None = Field(
        default=None,
        description="Override categories: {temp_id: category_id}",
    )
