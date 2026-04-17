"""
Analytics Pydantic schemas for request/response validation.
"""

from datetime import date
from decimal import Decimal
from typing import Literal, List
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


class SpendingSummary(BaseModel):
    """Monthly/yearly spending summary (alias: SpendingSummaryResponse)."""

    period_start: date
    period_end: date
    total_income: Decimal
    total_expenses: Decimal
    net_savings: Decimal
    savings_rate: float = Field(default=0.0, description="Savings as percentage of income")
    transaction_count: int = 0
    average_daily_spend: Decimal = Decimal("0")

    # Comparison with previous period
    income_change: float | None = None
    expense_change: float | None = None
    savings_change: float | None = None


# Alias for backwards compatibility
SpendingSummaryResponse = SpendingSummary


class CategorySpending(BaseModel):
    """Single category spending data."""

    category_id: str | None = None
    category_name: str
    category_icon: str | None = None
    category_color: str | None = None
    amount: Decimal
    percentage: float = 0.0
    transaction_count: int = 0
    average_transaction: Decimal = Decimal("0")
    previous_amount: Decimal | None = None
    change_percentage: float | None = None


# Alias
CategoryBreakdownItem = CategorySpending


class CategoryBreakdown(BaseModel):
    """Spending breakdown by category (alias: CategoryBreakdownResponse)."""

    period_start: date
    period_end: date
    total_amount: Decimal
    categories: list[CategorySpending] = []
    uncategorized_amount: Decimal = Decimal("0")
    uncategorized_count: int = 0


CategoryBreakdownResponse = CategoryBreakdown


class FocusCategoryItem(BaseModel):
    """Focused category item for key spend buckets."""

    category_id: str | None = None
    category_name: str
    amount: Decimal
    transaction_count: int = 0
    percentage: float = 0.0


class FocusCategoryResponse(BaseModel):
    """Response for key focus categories."""

    period_start: date
    period_end: date
    total_amount: Decimal
    categories: list[FocusCategoryItem] = []


class TrendDataPoint(BaseModel):
    """Single data point in trend."""

    date: date
    income: Decimal = Decimal("0")
    expenses: Decimal = Decimal("0")
    net: Decimal = Decimal("0")
    transaction_count: int = 0


class TrendData(BaseModel):
    """Spending trends over time (alias: SpendingTrendsResponse)."""

    period: str
    data_points: list[TrendDataPoint] = []
    average_income: Decimal = Decimal("0")
    average_expenses: Decimal = Decimal("0")
    average_spending: Decimal = Decimal("0")
    overall_trend: str | None = None
    highest_expense_date: date | None = None
    highest_expense_amount: Decimal | None = None
    lowest_expense_date: date | None = None
    lowest_expense_amount: Decimal | None = None


SpendingTrendsResponse = TrendData


class MonthlyComparison(BaseModel):
    """Monthly comparison data."""

    current_month: Decimal
    previous_month: Decimal
    change_percentage: float
    change_amount: Decimal


class Insight(BaseModel):
    """Single AI-generated insight (alias: InsightItem)."""

    id: str = ""
    type: str
    severity: str | None = None
    title: str
    message: str | None = None
    description: str | None = None
    action: str | None = None
    action_suggestion: str | None = None
    category: str | None = None
    amount: Decimal | None = None
    change_percentage: float | None = None
    priority: int = Field(default=0, description="Higher = more important")
    data: dict | None = None
    created_at: str | None = None


InsightItem = Insight


class InsightsList(BaseModel):
    """AI-generated insights response (alias: InsightsResponse)."""

    generated_at: date
    next_update: str | None = None
    insights: list[Insight] = []
    summary: str = ""


InsightsResponse = InsightsList


class ForecastDataPoint(BaseModel):
    """Predicted spending data point (alias: PredictionDataPoint)."""

    date: date
    predicted_amount: Decimal
    confidence_lower: Decimal
    confidence_upper: Decimal


PredictionDataPoint = ForecastDataPoint


class ForecastData(BaseModel):
    """Spending predictions response (alias: SpendingPredictionsResponse)."""

    predicted_monthly_expense: Decimal = Decimal("0")
    predicted_monthly_income: Decimal = Decimal("0")
    confidence_level: float = 0.8
    category_predictions: list[dict] = []
    daily_predictions: list[ForecastDataPoint] | None = None
    weekly_predictions: list[ForecastDataPoint] | None = None


SpendingPredictionsResponse = ForecastData


class BenchmarkItem(BaseModel):
    """Benchmark comparison item."""

    category: str
    user_amount: Decimal
    user_percentage: float
    average_amount: Decimal
    average_percentage: float
    percentile: int = Field(default=50, description="User's percentile (0-100)")
    status: Literal["below_average", "average", "above_average"] = "average"


class BenchmarkResponse(BaseModel):
    """User spending compared to averages."""

    period_start: date
    period_end: date
    user_total_expense: Decimal
    average_total_expense: Decimal
    overall_percentile: int = 50
    categories: list[BenchmarkItem] = []
    summary: str = ""


class MerchantSummary(BaseModel):
    """Single merchant analysis (alias: MerchantAnalysisItem)."""

    merchant_name: str
    total_amount: Decimal
    transaction_count: int = 0
    average_transaction: Decimal = Decimal("0")
    last_transaction_date: date | None = None
    category: str | None = None
    percentage_of_total: float = 0.0
    trend: Literal["increasing", "decreasing", "stable"] = "stable"


MerchantAnalysisItem = MerchantSummary


class MerchantAnalysisResponse(BaseModel):
    """Top merchants analysis."""

    period_start: date
    period_end: date
    merchants: list[MerchantSummary] = []
    total_merchant_count: int = 0


class RecurringTransactionItem(BaseModel):
    """Recurring transaction item."""

    merchant_name: str
    category: str | None = None
    amount: Decimal
    frequency: Literal["weekly", "biweekly", "monthly", "quarterly", "yearly"] = "monthly"
    next_expected_date: date | None = None
    last_occurrence: date | None = None
    is_confirmed: bool = Field(
        default=False,
        description="User confirmed as recurring",
    )
    transaction_count: int = 0


class RecurringTransactionsResponse(BaseModel):
    """Recurring transactions analysis."""

    total_monthly_recurring: Decimal = Decimal("0")
    recurring_transactions: list[RecurringTransactionItem] = []
    potential_savings: Decimal | None = None


class BudgetCategoryStatus(BaseModel):
    """Budget status for a single category."""

    budget_id: UUID | None = None
    category_id: UUID | None = None
    category_name: str
    budget_amount: Decimal
    spent_amount: Decimal
    remaining_amount: Decimal
    utilization_percentage: float = 0.0
    is_over_budget: bool = False
    projected_end_of_month: Decimal = Decimal("0")
    days_remaining: int = 0


class BudgetStatus(BaseModel):
    """Overall budget status."""

    period: str = "monthly"
    period_start: date
    period_end: date
    total_budget: Decimal
    total_spent: Decimal
    total_remaining: Decimal
    overall_utilization: float = 0.0
    categories: list[BudgetCategoryStatus] = []
    alerts: list[str] = []
