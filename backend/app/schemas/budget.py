"""
Budget Pydantic schemas for request/response validation.
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.budget import BudgetPeriod
from app.schemas.category import CategoryResponse
from app.schemas.common import BaseSchema, TimestampMixin


# ====================
# Request Schemas
# ====================


class BudgetCreateRequest(BaseModel):
    """Schema for creating a budget."""

    category_id: UUID | None = Field(
        default=None,
        description="Category ID (null for overall budget)",
    )
    amount_limit: Decimal = Field(
        ...,
        gt=0,
        description="Budget limit amount",
    )
    period: BudgetPeriod = Field(
        default=BudgetPeriod.MONTHLY,
        description="Budget period",
    )
    start_date: date = Field(..., description="Budget start date")
    end_date: date | None = Field(default=None, description="Budget end date")
    alert_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Alert threshold (0.0 - 1.0)",
    )
    alert_enabled: bool = Field(default=True)
    rollover_enabled: bool = Field(default=False)

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: date | None, info) -> date | None:
        """Validate that end_date is after start_date."""
        if v is not None and "start_date" in info.data:
            if v <= info.data["start_date"]:
                raise ValueError("end_date must be after start_date")
        return v


class BudgetUpdateRequest(BaseModel):
    """Schema for updating a budget."""

    amount_limit: Decimal | None = Field(default=None, gt=0)
    period: BudgetPeriod | None = None
    end_date: date | None = None
    alert_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    alert_enabled: bool | None = None
    rollover_enabled: bool | None = None
    is_active: bool | None = None


# ====================
# Response Schemas
# ====================


class BudgetResponse(BaseSchema, TimestampMixin):
    """Schema for budget response."""

    id: UUID
    user_id: UUID
    category_id: UUID | None
    category: CategoryResponse | None = None
    amount_limit: Decimal
    period: BudgetPeriod
    start_date: date
    end_date: date | None
    alert_threshold: float
    alert_enabled: bool
    is_active: bool
    rollover_enabled: bool
    rollover_amount: Decimal


class BudgetWithProgressResponse(BudgetResponse):
    """Budget response with spending progress."""

    spent_amount: Decimal = Decimal("0.00")
    remaining_amount: Decimal = Decimal("0.00")
    percentage_used: float = 0.0
    is_over_budget: bool = False
    is_alert_triggered: bool = False
    days_remaining: int | None = None
    projected_spend: Decimal | None = None


class BudgetSummaryResponse(BaseModel):
    """Summary of all budgets."""

    total_budgeted: Decimal
    total_spent: Decimal
    total_remaining: Decimal
    overall_percentage_used: float
    budgets_on_track: int
    budgets_at_risk: int
    budgets_over: int
