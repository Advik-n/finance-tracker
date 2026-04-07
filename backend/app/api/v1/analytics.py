"""
Analytics Endpoints

Provides spending insights, trends, forecasts, and financial analytics.
"""

import logging
from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Query

from app.api.deps import ActiveUser, DatabaseSession
from app.models.transaction import TransactionType
from app.schemas.analytics import (
    BenchmarkResponse,
    CategoryBreakdownResponse,
    InsightsResponse,
    MerchantAnalysisResponse,
    RecurringTransactionsResponse,
    SpendingPredictionsResponse,
    SpendingSummaryResponse,
    SpendingTrendsResponse,
)
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analytics"])


@router.get(
    "/summary",
    response_model=SpendingSummaryResponse,
    summary="Get spending summary",
    description="Get income, expense, and savings summary for a period.",
)
async def get_spending_summary(
    current_user: ActiveUser,
    db: DatabaseSession,
    start_date: Optional[date] = Query(default=None, description="Period start date"),
    end_date: Optional[date] = Query(default=None, description="Period end date"),
    compare_previous: bool = Query(default=True, description="Compare with previous period"),
) -> SpendingSummaryResponse:
    """
    Get spending summary including:
    - Total income and expenses
    - Net savings and savings rate
    - Average daily spending
    - Comparison with previous period (if enabled)
    """
    service = AnalyticsService(db)
    return await service.get_spending_summary(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        compare_previous=compare_previous,
    )


@router.get(
    "/category-breakdown",
    response_model=CategoryBreakdownResponse,
    summary="Get category breakdown",
    description="Get spending breakdown by category.",
)
async def get_category_breakdown(
    current_user: ActiveUser,
    db: DatabaseSession,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    transaction_type: TransactionType = Query(
        default=TransactionType.DEBIT,
        description="DEBIT for expenses, CREDIT for income",
    ),
) -> CategoryBreakdownResponse:
    """
    Get spending/income breakdown by category.

    Shows:
    - Amount and percentage per category
    - Transaction count per category
    - Average transaction per category
    """
    service = AnalyticsService(db)
    return await service.get_category_breakdown(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        transaction_type=transaction_type,
    )


@router.get(
    "/trends",
    response_model=SpendingTrendsResponse,
    summary="Get spending trends",
    description="Get spending trends over time.",
)
async def get_spending_trends(
    current_user: ActiveUser,
    db: DatabaseSession,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    period: Literal["daily", "weekly", "monthly"] = Query(
        default="monthly",
        description="Aggregation period",
    ),
) -> SpendingTrendsResponse:
    """
    Get spending trends aggregated by day, week, or month.

    Shows:
    - Income, expense, and net for each period
    - Overall statistics (averages, highs, lows)
    """
    service = AnalyticsService(db)
    return await service.get_spending_trends(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        period=period,
    )


@router.get(
    "/insights",
    response_model=InsightsResponse,
    summary="Get AI insights",
    description="Get AI-generated financial insights and recommendations.",
)
async def get_insights(
    current_user: ActiveUser,
    db: DatabaseSession,
) -> InsightsResponse:
    """
    Get AI-powered financial insights including:

    - Spending pattern analysis
    - Savings recommendations
    - Category-specific insights
    - Alerts for unusual spending
    - Actionable suggestions

    Examples:
    - "Petrol spending: ₹4,200/month (↑12% from last month)"
    - "You spend 68% more on fast food than average"
    - "Consider reviewing your subscription expenses"
    """
    service = AnalyticsService(db)
    return await service.get_insights(user_id=current_user.id)


@router.get(
    "/predictions",
    response_model=SpendingPredictionsResponse,
    summary="Get spending predictions",
    description="Get predicted spending for upcoming periods.",
)
async def get_spending_predictions(
    current_user: ActiveUser,
    db: DatabaseSession,
) -> SpendingPredictionsResponse:
    """
    Get spending predictions based on historical data.

    Returns:
    - Predicted monthly income and expenses
    - Confidence level of predictions
    - Category-specific predictions
    """
    service = AnalyticsService(db)
    return await service.get_spending_predictions(user_id=current_user.id)


@router.get(
    "/benchmark",
    response_model=BenchmarkResponse,
    summary="Get benchmark comparison",
    description="Compare spending with platform averages.",
)
async def get_benchmark_comparison(
    current_user: ActiveUser,
    db: DatabaseSession,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
) -> BenchmarkResponse:
    """
    Compare your spending with other users.

    Shows:
    - Category-by-category comparison
    - Your percentile ranking
    - Areas where you spend more/less than average
    """
    service = AnalyticsService(db)
    return await service.get_benchmark_comparison(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/merchant-analysis",
    response_model=MerchantAnalysisResponse,
    summary="Get merchant analysis",
    description="Analyze spending by merchant.",
)
async def get_merchant_analysis(
    current_user: ActiveUser,
    db: DatabaseSession,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50, description="Number of merchants"),
) -> MerchantAnalysisResponse:
    """
    Get analysis of top merchants by spending.

    Shows:
    - Total amount per merchant
    - Transaction count and average
    - Percentage of total spending
    - Spending trend (increasing/decreasing)
    """
    service = AnalyticsService(db)
    return await service.get_merchant_analysis(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


@router.get(
    "/recurring",
    response_model=RecurringTransactionsResponse,
    summary="Get recurring transactions",
    description="Identify recurring transactions and subscriptions.",
)
async def get_recurring_transactions(
    current_user: ActiveUser,
    db: DatabaseSession,
) -> RecurringTransactionsResponse:
    """
    Identify recurring transactions like:
    - Monthly subscriptions (Netflix, Spotify, etc.)
    - Utility bills
    - EMIs and loan payments
    - Regular transfers

    Shows:
    - Total monthly recurring amount
    - Frequency detection (weekly, monthly, etc.)
    - Next expected date
    """
    service = AnalyticsService(db)
    return await service.get_recurring_transactions(user_id=current_user.id)
