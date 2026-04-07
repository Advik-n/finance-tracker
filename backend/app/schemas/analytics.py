"""
Analytics Pydantic schemas for request/response validation.
"""

from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


# ====================
# Request Schemas
# ====================


class AnalyticsPeriodParams(BaseModel):
    """Common period parameters for analytics."""

    start_date: date | None = Field(default=None, description="Start date for analysis")
    end_date: date | None = Field(default=None, description="End date for analysis")
    period: Literal["daily", "weekly", "monthly", "yearly"] = Field(
        default="monthly",
        description="Aggregation period",
    )


class TrendParams(AnalyticsPeriodParams):
    """Parameters for trend analysis."""

    compare_with_previous: bool = Field(
        default=True,
        description="Compare with previous period",
    )
    include_forecast: bool = Field(default=False, description="Include predictions")


# ====================
# Response Schemas
# ====================


class SpendingSummaryResponse(BaseModel):
    """Monthly/yearly spending summary."""

    period_start: date
    period_end: date
    total_income: Decimal
    total_expenses: Decimal
    net_savings: Decimal
    savings_rate: float = Field(..., description="Savings as percentage of income")
    transaction_count: int
    average_daily_spend: Decimal

    # Comparison with previous period
    income_change: float | None = None  # Percentage change
    expense_change: float | None = None
    savings_change: float | None = None


class CategoryBreakdownItem(BaseModel):
    """Single category in breakdown."""

    category_id: str | None
    category_name: str
    category_icon: str | None = None
    category_color: str | None = None
    amount: Decimal
    percentage: float
    transaction_count: int
    average_transaction: Decimal

    # Comparison
    previous_amount: Decimal | None = None
    change_percentage: float | None = None


class CategoryBreakdownResponse(BaseModel):
    """Spending breakdown by category."""

    period_start: date
    period_end: date
    total_amount: Decimal
    categories: list[CategoryBreakdownItem]


class TrendDataPoint(BaseModel):
    """Single data point in trend."""

    date: date
    income: Decimal
    expenses: Decimal
    net: Decimal
    transaction_count: int


class SpendingTrendsResponse(BaseModel):
    """Spending trends over time."""

    period: str
    data_points: list[TrendDataPoint]

    # Summary statistics
    average_income: Decimal
    average_expenses: Decimal
    highest_expense_date: date | None = None
    highest_expense_amount: Decimal | None = None
    lowest_expense_date: date | None = None
    lowest_expense_amount: Decimal | None = None


class InsightItem(BaseModel):
    """Single AI-generated insight."""

    id: str
    type: Literal["info", "warning", "success", "alert"]
    title: str
    message: str
    category: str | None = None
    amount: Decimal | None = None
    change_percentage: float | None = None
    action_suggestion: str | None = None
    priority: int = Field(default=0, description="Higher = more important")


class InsightsResponse(BaseModel):
    """AI-generated insights response."""

    generated_at: date
    insights: list[InsightItem]
    summary: str


class PredictionDataPoint(BaseModel):
    """Predicted spending data point."""

    date: date
    predicted_amount: Decimal
    confidence_lower: Decimal
    confidence_upper: Decimal


class SpendingPredictionsResponse(BaseModel):
    """Spending predictions response."""

    predicted_monthly_expense: Decimal
    predicted_monthly_income: Decimal
    confidence_level: float

    # Category predictions
    category_predictions: list[dict]

    # Time series predictions
    daily_predictions: list[PredictionDataPoint] | None = None
    weekly_predictions: list[PredictionDataPoint] | None = None


class BenchmarkItem(BaseModel):
    """Benchmark comparison item."""

    category: str
    user_amount: Decimal
    user_percentage: float
    average_amount: Decimal
    average_percentage: float
    percentile: int = Field(..., description="User's percentile (0-100)")
    status: Literal["below_average", "average", "above_average"]


class BenchmarkResponse(BaseModel):
    """User spending compared to averages."""

    period_start: date
    period_end: date
    user_total_expense: Decimal
    average_total_expense: Decimal
    overall_percentile: int
    categories: list[BenchmarkItem]
    summary: str


class MerchantAnalysisItem(BaseModel):
    """Single merchant analysis."""

    merchant_name: str
    total_amount: Decimal
    transaction_count: int
    average_transaction: Decimal
    last_transaction_date: date
    category: str | None = None
    percentage_of_total: float
    trend: Literal["increasing", "decreasing", "stable"]


class MerchantAnalysisResponse(BaseModel):
    """Top merchants analysis."""

    period_start: date
    period_end: date
    merchants: list[MerchantAnalysisItem]
    total_merchant_count: int


class RecurringTransactionItem(BaseModel):
    """Recurring transaction item."""

    merchant_name: str
    category: str | None = None
    amount: Decimal
    frequency: Literal["weekly", "biweekly", "monthly", "quarterly", "yearly"]
    next_expected_date: date | None = None
    last_occurrence: date
    is_confirmed: bool = Field(
        default=False,
        description="User confirmed as recurring",
    )
    transaction_count: int


class RecurringTransactionsResponse(BaseModel):
    """Recurring transactions analysis."""

    total_monthly_recurring: Decimal
    recurring_transactions: list[RecurringTransactionItem]
    potential_savings: Decimal | None = None


class BudgetCategoryStatus(BaseModel):
    """Budget status for a single category."""

    budget_id: UUID
    category_id: UUID | None
    category_name: str
    budget_amount: Decimal
    spent_amount: Decimal
    remaining_amount: Decimal
    utilization_percentage: float
    is_over_budget: bool
    projected_end_of_month: Decimal
    days_remaining: int


class BudgetStatus(BaseModel):
    """Overall budget status."""

    period: str
    period_start: date
    period_end: date
    total_budget: Decimal
    total_spent: Decimal
    total_remaining: Decimal
    overall_utilization: float
    categories: list[BudgetCategoryStatus]
    alerts: list[str]
