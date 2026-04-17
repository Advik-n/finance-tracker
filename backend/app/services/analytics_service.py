"""
Analytics Service

Provides spending analytics, trends, and AI-powered insights.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, and_, or_, extract, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.transaction import Transaction, TransactionType
from app.models.category import Category
from app.models.budget import Budget
from app.schemas.analytics import (
    SpendingSummary,
    CategoryBreakdown,
    CategorySpending,
    FocusCategoryItem,
    FocusCategoryResponse,
    TrendData,
    TrendDataPoint,
    MonthlyComparison,
    ForecastData,
    ForecastDataPoint,
    InsightsList,
    Insight,
    BudgetStatus,
    BudgetCategoryStatus,
    MerchantSummary,
)
from app.ml.insights_engine import InsightsEngine
from app.ml.predictor import SpendingPredictor
from app.utils.helpers import generate_slug


class AnalyticsService:
    """
    Service class for financial analytics.
    
    Provides spending summaries, trends, forecasts, and insights.
    """

    FOCUS_ALIASES = {
        "clothes": "clothes-apparel",
        "clothing": "clothes-apparel",
        "apparel": "clothes-apparel",
        "gas": "petrol",
        "fuel": "petrol",
        "grocery": "groceries",
        "food": "food-dining",
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.insights_engine = InsightsEngine()
        self.predictor = SpendingPredictor()
    
    async def get_spending_summary(
        self,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        compare_previous: bool = True,
    ) -> SpendingSummary:
        """
        Get spending summary for a period.
        
        Args:
            user_id: User UUID
            start_date: Period start (defaults to month start)
            end_date: Period end (defaults to today)
            
        Returns:
            SpendingSummary with totals and averages
        """
        today = date.today()
        if not end_date:
            end_date = today
        if not start_date:
            start_date = date(today.year, today.month, 1)
        
        # Query for totals
        result = await self.db.execute(
            select(
                func.sum(
                    case(
                        (Transaction.transaction_type == TransactionType.CREDIT, Transaction.amount),
                        else_=Decimal("0")
                    )
                ).label("total_income"),
                func.sum(
                    case(
                        (Transaction.transaction_type == TransactionType.DEBIT, Transaction.amount),
                        else_=Decimal("0")
                    )
                ).label("total_expenses"),
                func.count().label("transaction_count"),
                func.max(
                    case(
                        (Transaction.transaction_type == TransactionType.DEBIT, Transaction.amount),
                        else_=None
                    )
                ).label("largest_expense"),
                func.max(
                    case(
                        (Transaction.transaction_type == TransactionType.CREDIT, Transaction.amount),
                        else_=None
                    )
                ).label("largest_income"),
            )
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date,
                    Transaction.is_deleted == False,  # noqa: E712
                )
            )
        )
        
        row = result.first()
        
        total_income = row.total_income or Decimal("0")
        total_expenses = row.total_expenses or Decimal("0")
        net_savings = total_income - total_expenses
        transaction_count = row.transaction_count or 0
        
        savings_rate = 0.0
        if total_income > 0:
            savings_rate = float(net_savings / total_income * 100)
        
        days_in_period = max((end_date - start_date).days + 1, 1)
        average_daily_spend = total_expenses / days_in_period

        income_change = None
        expense_change = None
        savings_change = None

        if compare_previous:
            prev_start = start_date - timedelta(days=days_in_period)
            prev_end = start_date - timedelta(days=1)

            prev_result = await self.db.execute(
                select(
                    func.sum(
                        case(
                            (Transaction.transaction_type == TransactionType.CREDIT, Transaction.amount),
                            else_=Decimal("0"),
                        )
                    ).label("total_income"),
                    func.sum(
                        case(
                            (Transaction.transaction_type == TransactionType.DEBIT, Transaction.amount),
                            else_=Decimal("0"),
                        )
                    ).label("total_expenses"),
                )
                .where(
                    and_(
                        Transaction.user_id == user_id,
                        Transaction.transaction_date >= prev_start,
                        Transaction.transaction_date <= prev_end,
                        Transaction.is_deleted == False,  # noqa: E712
                    )
                )
            )
            prev_row = prev_result.first()
            prev_income = prev_row.total_income or Decimal("0")
            prev_expenses = prev_row.total_expenses or Decimal("0")
            prev_savings = prev_income - prev_expenses

            def pct_change(current: Decimal, previous: Decimal) -> float:
                if previous == 0:
                    return 100.0 if current > 0 else 0.0
                return float((current - previous) / previous * 100)

            income_change = round(pct_change(total_income, prev_income), 2)
            expense_change = round(pct_change(total_expenses, prev_expenses), 2)
            savings_change = round(pct_change(net_savings, prev_savings), 2)

        return SpendingSummary(
            period_start=start_date,
            period_end=end_date,
            total_income=total_income,
            total_expenses=total_expenses,
            net_savings=net_savings,
            savings_rate=round(savings_rate, 2),
            transaction_count=transaction_count,
            average_daily_spend=average_daily_spend,
            income_change=income_change,
            expense_change=expense_change,
            savings_change=savings_change,
        )
    
    async def get_category_breakdown(
        self,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        transaction_type: TransactionType = TransactionType.DEBIT,
    ) -> CategoryBreakdown:
        """
        Get spending breakdown by category.
        
        Args:
            user_id: User UUID
            start_date: Period start
            end_date: Period end
            
        Returns:
            CategoryBreakdown with per-category data
        """
        today = date.today()
        if not end_date:
            end_date = today
        if not start_date:
            start_date = date(today.year, today.month, 1)
        
        parent = aliased(Category)
        group_id = case(
            (Category.parent_id.is_not(None), Category.parent_id),
            else_=Category.id,
        )

        # Query category spending grouped by parent category
        result = await self.db.execute(
            select(
                group_id.label("id"),
                parent.name,
                parent.icon,
                parent.color,
                func.sum(Transaction.amount).label("amount"),
                func.count().label("count"),
            )
            .join(Transaction, Transaction.category_id == Category.id)
            .join(parent, parent.id == group_id)
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date,
                    Transaction.transaction_type == transaction_type,
                    Transaction.is_deleted == False,  # noqa: E712
                )
            )
            .group_by(group_id, parent.name, parent.icon, parent.color)
            .order_by(func.sum(Transaction.amount).desc())
        )
        
        rows = result.all()
        
        # Calculate totals
        total_amount = sum(row.amount for row in rows)
        
        # Get uncategorized transactions
        uncategorized_result = await self.db.execute(
            select(
                func.sum(Transaction.amount),
                func.count(),
            )
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date,
                    Transaction.transaction_type == transaction_type,
                    Transaction.is_deleted == False,  # noqa: E712
                    Transaction.category_id == None,
                )
            )
        )
        uncat_row = uncategorized_result.first()
        uncategorized_amount = uncat_row[0] or Decimal("0")
        uncategorized_count = uncat_row[1] or 0
        
        total_amount += uncategorized_amount
        
        categories = []
        for row in rows:
            percentage = 0.0
            if total_amount > 0:
                percentage = float(row.amount / total_amount * 100)
            
            avg_transaction = Decimal("0")
            if row.count > 0:
                avg_transaction = row.amount / row.count
            
            categories.append(CategorySpending(
                category_id=row.id,
                category_name=row.name,
                category_icon=row.icon,
                category_color=row.color,
                amount=row.amount,
                percentage=round(percentage, 2),
                transaction_count=row.count,
                average_transaction=avg_transaction,
            ))
        
        return CategoryBreakdown(
            period_start=start_date,
            period_end=end_date,
            total_amount=total_amount,
            categories=categories,
            uncategorized_amount=uncategorized_amount,
            uncategorized_count=uncategorized_count,
        )

    async def get_focus_categories(
        self,
        user_id: UUID,
        names: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> FocusCategoryResponse:
        today = date.today()
        if not end_date:
            end_date = today
        if not start_date:
            start_date = date(today.year, today.month, 1)

        normalized_slugs = []
        normalized_names = []
        for name in names:
            if not name:
                continue
            slug = generate_slug(name)
            slug = self.FOCUS_ALIASES.get(slug, slug)
            normalized_slugs.append(slug)
            normalized_names.append(name.lower())

        if not normalized_slugs and not normalized_names:
            return FocusCategoryResponse(
                period_start=start_date,
                period_end=end_date,
                total_amount=Decimal("0"),
                categories=[],
            )

        categories_result = await self.db.execute(
            select(Category)
            .where(
                or_(
                    Category.slug.in_(normalized_slugs),
                    func.lower(Category.name).in_(normalized_names),
                )
            )
        )
        categories = list(categories_result.scalars().all())
        if not categories:
            return FocusCategoryResponse(
                period_start=start_date,
                period_end=end_date,
                total_amount=Decimal("0"),
                categories=[],
            )

        category_ids = [c.id for c in categories]
        totals_result = await self.db.execute(
            select(
                Category.id,
                Category.name,
                func.sum(Transaction.amount).label("amount"),
                func.count().label("count"),
            )
            .join(Transaction, Transaction.category_id == Category.id)
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date,
                    Transaction.transaction_type == TransactionType.DEBIT,
                    Transaction.is_deleted == False,  # noqa: E712
                    Transaction.category_id.in_(category_ids),
                )
            )
            .group_by(Category.id, Category.name)
            .order_by(func.sum(Transaction.amount).desc())
        )
        rows = totals_result.all()

        total_amount = sum(row.amount for row in rows) if rows else Decimal("0")
        items: List[FocusCategoryItem] = []
        for row in rows:
            percentage = 0.0
            if total_amount > 0:
                percentage = float(row.amount / total_amount * 100)
            items.append(
                FocusCategoryItem(
                    category_id=str(row.id),
                    category_name=row.name,
                    amount=row.amount,
                    transaction_count=row.count,
                    percentage=percentage,
                )
            )

        return FocusCategoryResponse(
            period_start=start_date,
            period_end=end_date,
            total_amount=total_amount,
            categories=items,
        )
    
    async def get_spending_trends(
        self,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period: str = "monthly",
    ) -> TrendData:
        """
        Get spending trends over time.
        
        Args:
            user_id: User UUID
            period: Aggregation period
            months: Number of months to analyze
            
        Returns:
            TrendData with time series
        """
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=180)
        
        # Query based on period
        if period == "monthly":
            result = await self.db.execute(
                select(
                    extract("year", Transaction.transaction_date).label("year"),
                    extract("month", Transaction.transaction_date).label("month"),
                    func.sum(
                        case(
                            (Transaction.transaction_type == TransactionType.CREDIT, Transaction.amount),
                            else_=Decimal("0")
                        )
                    ).label("income"),
                    func.sum(
                        case(
                            (Transaction.transaction_type == TransactionType.DEBIT, Transaction.amount),
                            else_=Decimal("0")
                        )
                    ).label("expenses"),
                    func.count().label("count"),
                )
                .where(
                    and_(
                        Transaction.user_id == user_id,
                        Transaction.transaction_date >= start_date,
                        Transaction.transaction_date <= end_date,
                        Transaction.is_deleted == False,  # noqa: E712
                    )
                )
                .group_by(
                    extract("year", Transaction.transaction_date),
                    extract("month", Transaction.transaction_date),
                )
                .order_by(
                    extract("year", Transaction.transaction_date),
                    extract("month", Transaction.transaction_date),
                )
            )
        else:
            # Daily or weekly aggregation
            date_field = (
                func.date_trunc("week", Transaction.transaction_date)
                if period == "weekly"
                else func.date(Transaction.transaction_date)
            )
            result = await self.db.execute(
                select(
                    date_field.label("date"),
                    func.sum(
                        case(
                            (Transaction.transaction_type == TransactionType.CREDIT, Transaction.amount),
                            else_=Decimal("0")
                        )
                    ).label("income"),
                    func.sum(
                        case(
                            (Transaction.transaction_type == TransactionType.DEBIT, Transaction.amount),
                            else_=Decimal("0")
                        )
                    ).label("expenses"),
                    func.count().label("count"),
                )
                .where(
                    and_(
                        Transaction.user_id == user_id,
                        Transaction.transaction_date >= start_date,
                        Transaction.transaction_date <= end_date,
                        Transaction.is_deleted == False,  # noqa: E712
                    )
                )
                .group_by(date_field)
                .order_by(date_field)
            )
        
        rows = result.all()
        
        data_points = []
        total_spending = Decimal("0")
        
        for row in rows:
            if period == "monthly":
                point_date = date(int(row.year), int(row.month), 1)
            else:
                point_date = row.date.date() if hasattr(row.date, "date") else row.date

            income = row.income or Decimal("0")
            expenses = row.expenses or Decimal("0")
            total_spending += expenses

            data_points.append(TrendDataPoint(
                date=point_date,
                income=income,
                expenses=expenses,
                net=income - expenses,
                transaction_count=row.count,
            ))
        
        avg_income = Decimal("0")
        avg_expenses = Decimal("0")
        average_spending = Decimal("0")
        if data_points:
            avg_income = sum(dp.income for dp in data_points) / len(data_points)
            avg_expenses = sum(dp.expenses for dp in data_points) / len(data_points)
            average_spending = total_spending / len(data_points)

        overall_trend = "stable"
        if len(data_points) >= 2:
            first_half = sum(dp.expenses for dp in data_points[:len(data_points)//2])
            second_half = sum(dp.expenses for dp in data_points[len(data_points)//2:])
            if second_half > first_half * Decimal("1.1"):
                overall_trend = "increasing"
            elif second_half < first_half * Decimal("0.9"):
                overall_trend = "decreasing"

        highest_expense_date = None
        highest_expense_amount = None
        lowest_expense_date = None
        lowest_expense_amount = None
        if data_points:
            highest = max(data_points, key=lambda dp: dp.expenses)
            lowest = min(data_points, key=lambda dp: dp.expenses)
            highest_expense_date = highest.date
            highest_expense_amount = highest.expenses
            lowest_expense_date = lowest.date
            lowest_expense_amount = lowest.expenses

        return TrendData(
            period=period,
            data_points=data_points,
            average_income=avg_income,
            average_expenses=avg_expenses,
            average_spending=average_spending,
            overall_trend=overall_trend,
            highest_expense_date=highest_expense_date,
            highest_expense_amount=highest_expense_amount,
            lowest_expense_date=lowest_expense_date,
            lowest_expense_amount=lowest_expense_amount,
        )
    
    async def get_monthly_comparison(self, user_id: UUID) -> MonthlyComparison:
        """
        Compare current month to previous month.
        
        Args:
            user_id: User UUID
            
        Returns:
            MonthlyComparison data
        """
        today = date.today()
        current_month_start = date(today.year, today.month, 1)
        
        if today.month == 1:
            prev_month_start = date(today.year - 1, 12, 1)
        else:
            prev_month_start = date(today.year, today.month - 1, 1)
        
        prev_month_end = current_month_start - timedelta(days=1)
        
        current = await self.get_spending_summary(
            user_id, current_month_start, today
        )
        previous = await self.get_spending_summary(
            user_id, prev_month_start, prev_month_end
        )
        
        def calc_change(current_val: Decimal, prev_val: Decimal) -> float:
            if prev_val == 0:
                return 100.0 if current_val > 0 else 0.0
            return float((current_val - prev_val) / prev_val * 100)
        
        return MonthlyComparison(
            current_month=current_month_start.strftime("%Y-%m"),
            previous_month=prev_month_start.strftime("%Y-%m"),
            current_income=current.total_income,
            previous_income=previous.total_income,
            income_change=round(calc_change(current.total_income, previous.total_income), 2),
            current_expenses=current.total_expenses,
            previous_expenses=previous.total_expenses,
            expenses_change=round(calc_change(current.total_expenses, previous.total_expenses), 2),
            current_savings=current.net_savings,
            previous_savings=previous.net_savings,
            savings_change=round(calc_change(current.net_savings, previous.net_savings), 2),
            category_changes=[],
        )
    
    async def get_spending_forecast(
        self,
        user_id: UUID,
        months_ahead: int = 3,
    ) -> ForecastData:
        """
        Get AI-powered spending forecast.
        
        Args:
            user_id: User UUID
            months_ahead: Months to forecast
            
        Returns:
            ForecastData with predictions
        """
        # Get historical data
        trends = await self.get_spending_trends(user_id, "monthly", 12)
        
        # Use predictor for forecast
        forecasts = self.predictor.forecast(
            historical_data=[dp.expenses for dp in trends.data_points],
            months_ahead=months_ahead,
        )
        
        return ForecastData(
            forecast_periods=forecasts,
            model_confidence=0.75,
            based_on_months=len(trends.data_points),
            assumptions=[
                "Based on historical spending patterns",
                "Assumes no major lifestyle changes",
                "Seasonal adjustments applied",
            ],
        )
    
    async def get_insights(self, user_id: UUID) -> InsightsList:
        """
        Get AI-generated financial insights.
        
        Args:
            user_id: User UUID
            
        Returns:
            InsightsList with recommendations
        """
        # Gather data for insights
        summary = await self.get_spending_summary(user_id)
        trends = await self.get_spending_trends(user_id)
        categories = await self.get_category_breakdown(user_id)
        
        # Generate insights
        insights = self.insights_engine.generate_insights(
            summary=summary,
            trends=trends,
            categories=categories,
        )
        
        now = datetime.utcnow()
        return InsightsList(
            insights=insights,
            generated_at=now.date(),
            next_update=(now + timedelta(hours=24)).isoformat(),
        )
    
    async def get_budget_status(self, user_id: UUID) -> BudgetStatus:
        """
        Get current budget status.
        
        Args:
            user_id: User UUID
            
        Returns:
            BudgetStatus with utilization
        """
        today = date.today()
        month_start = date(today.year, today.month, 1)
        
        # Get budgets
        result = await self.db.execute(
            select(Budget)
            .where(Budget.user_id == user_id)
        )
        budgets = result.scalars().all()
        
        # Get spending by category
        spending = await self.get_category_breakdown(
            user_id,
            month_start,
            today,
            transaction_type=TransactionType.DEBIT,
        )
        spending_by_category = {c.category_id: c.amount for c in spending.categories}
        
        total_budget = Decimal("0")
        total_spent = Decimal("0")
        categories = []
        alerts = []
        
        for budget in budgets:
            spent = spending_by_category.get(budget.category_id, Decimal("0"))
            remaining = budget.amount - spent
            utilization = 0.0
            if budget.amount > 0:
                utilization = float(spent / budget.amount * 100)
            
            total_budget += budget.amount
            total_spent += spent
            
            # Days remaining in period
            if budget.period == "monthly":
                import calendar
                _, last_day = calendar.monthrange(today.year, today.month)
                days_remaining = last_day - today.day
            else:
                days_remaining = 7 - today.weekday()
            
            # Project end of month spending
            if today.day > 0:
                daily_rate = spent / today.day
                projected = daily_rate * 30  # Approximate
            else:
                projected = spent
            
            is_over = spent > budget.amount
            
            category_status = BudgetCategoryStatus(
                budget_id=budget.id,
                category_id=budget.category_id,
                category_name=budget.name,
                budget_amount=budget.amount,
                spent_amount=spent,
                remaining_amount=remaining,
                utilization_percentage=round(utilization, 2),
                is_over_budget=is_over,
                projected_end_of_month=projected,
                days_remaining=days_remaining,
            )
            categories.append(category_status)
            
            # Generate alerts
            if is_over:
                alerts.append(f"Over budget on {budget.name}")
            elif utilization >= budget.alert_threshold:
                alerts.append(f"{budget.name} at {utilization:.0f}% of budget")
        
        overall_utilization = 0.0
        if total_budget > 0:
            overall_utilization = float(total_spent / total_budget * 100)
        
        return BudgetStatus(
            period="monthly",
            period_start=month_start,
            period_end=today,
            total_budget=total_budget,
            total_spent=total_spent,
            total_remaining=total_budget - total_spent,
            overall_utilization=round(overall_utilization, 2),
            categories=categories,
            alerts=alerts,
        )
    
    async def get_top_merchants(
        self,
        user_id: UUID,
        limit: int = 10,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[MerchantSummary]:
        """
        Get top merchants by spending.
        
        Args:
            user_id: User UUID
            limit: Number of merchants
            start_date: Period start
            end_date: Period end
            
        Returns:
            List of MerchantSummary
        """
        today = date.today()
        if not end_date:
            end_date = today
        if not start_date:
            start_date = date(today.year, today.month, 1)
        
        result = await self.db.execute(
            select(
                Transaction.merchant_name,
                func.sum(Transaction.amount).label("total"),
                func.count().label("count"),
                func.max(Transaction.transaction_date).label("last_date"),
            )
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date,
                    Transaction.transaction_type == TransactionType.DEBIT,
                    Transaction.merchant_name != None,
                    Transaction.is_deleted == False,  # noqa: E712
                )
            )
            .group_by(Transaction.merchant_name)
            .order_by(func.sum(Transaction.amount).desc())
            .limit(limit)
        )
        
        rows = result.all()
        
        merchants = []
        for row in rows:
            avg = Decimal("0")
            if row.count > 0:
                avg = row.total / row.count
            
            merchants.append(MerchantSummary(
                merchant_name=row.merchant_name,
                total_amount=row.total,
                transaction_count=row.count,
                average_transaction=avg,
                last_transaction_date=row.last_date,
                primary_category=None,
            ))
        
        return merchants
