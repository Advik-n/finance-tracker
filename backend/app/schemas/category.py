"""
Category Pydantic schemas for request/response validation.
"""

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema, TimestampMixin


# ====================
# Request Schemas
# ====================


class CategoryCreateRequest(BaseModel):
    """Schema for creating a category."""

    name: str = Field(..., min_length=1, max_length=100)
    parent_id: UUID | None = Field(default=None, description="Parent category ID")
    description: str | None = Field(default=None, max_length=500)
    icon: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$")
    is_income: bool = Field(default=False, description="Is this an income category?")
    keywords: list[str] | None = Field(default_factory=list)
    merchant_patterns: list[str] | None = Field(default_factory=list)


class CategoryUpdateRequest(BaseModel):
    """Schema for updating a category."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    parent_id: UUID | None = None
    description: str | None = None
    icon: str | None = None
    color: str | None = Field(default=None, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$")
    keywords: list[str] | None = None
    merchant_patterns: list[str] | None = None
    display_order: int | None = None


# ====================
# Response Schemas
# ====================


class CategoryResponse(BaseSchema, TimestampMixin):
    """Schema for category response."""

    id: UUID
    name: str
    slug: str
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    is_system: bool
    is_income: bool
    is_active: bool
    display_order: int
    parent_id: UUID | None = None
    keywords: list[str] = []
    merchant_patterns: list[str] = []


class CategoryWithChildrenResponse(CategoryResponse):
    """Category response with children."""

    children: list["CategoryResponse"] = []


class CategoryWithStatsResponse(CategoryResponse):
    """Category response with transaction statistics."""

    transaction_count: int = 0
    total_amount: float = 0.0
    percentage_of_total: float = 0.0


class CategoryTreeResponse(BaseModel):
    """Hierarchical category tree response."""

    income_categories: list[CategoryWithChildrenResponse]
    expense_categories: list[CategoryWithChildrenResponse]
