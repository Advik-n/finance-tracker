"""
Analytics Service

Provides spending analytics, trends, and AI-powered insights.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.models.category import Category
from app.models.budget import Budget
from app.schemas.analytics import (
    SpendingSummary,
    CategoryBreakdown,
    CategorySpending,
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


class AnalyticsService:
    """
    Service class for financial analytics.
    
    Provides spending summaries, trends, forecasts, and insights.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.insights_engine = InsightsEngine()
        self.predictor = SpendingPredictor()
    
    async def get_spending_summary(
        self,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
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
                    func.case(
                        (Transaction.transaction_type == "income", Transaction.amount),
                        else_=Decimal("0")
                    )
                ).label("total_income"),
                func.sum(
                    func.case(
                        (Transaction.transaction_type == "expense", Transaction.amount),
                        else_=Decimal("0")
                    )
                ).label("total_expenses"),
                func.count().label("transaction_count"),
                func.max(
                    func.case(
                        (Transaction.transaction_type == "expense", Transaction.amount),
                        else_=None
                    )
                ).label("largest_expense"),
                func.max(
                    func.case(
                        (Transaction.transaction_type == "income", Transaction.amount),
                        else_=None
                    )
                ).label("largest_income"),
            )
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date,
                    Transaction.is_excluded == False,
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
        
        average_transaction = Decimal("0")
        if transaction_count > 0:
            average_transaction = (total_income + total_expenses) / transaction_count
        
        return SpendingSummary(
            period_start=start_date,
            period_end=end_date,
            total_income=total_income,
            total_expenses=total_expenses,
            net_savings=net_savings,
            savings_rate=round(savings_rate, 2),
            transaction_count=transaction_count,
            average_transaction=average_transaction,
            largest_expense=row.largest_expense,
            largest_income=row.largest_income,
        )
    
    async def get_category_breakdown(
        self,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
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
        
        # Query category spending
        result = await self.db.execute(
            select(
                Category.id,
                Category.name,
                Category.icon,
                Category.color,
                func.sum(Transaction.amount).label("amount"),
                func.count().label("count"),
            )
            .join(Transaction, Transaction.category_id == Category.id)
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date,
                    Transaction.transaction_type == "expense",
                    Transaction.is_excluded == False,
                )
            )
            .group_by(Category.id, Category.name, Category.icon, Category.color)
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
                    Transaction.transaction_type == "expense",
                    Transaction.is_excluded == False,
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
    
    async def get_spending_trends(
        self,
        user_id: UUID,
        period: str = "monthly",
        months: int = 6,
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
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)
        
        # Query based on period
        if period == "monthly":
            result = await self.db.execute(
                select(
                    extract("year", Transaction.transaction_date).label("year"),
                    extract("month", Transaction.transaction_date).label("month"),
                    func.sum(
                        func.case(
                            (Transaction.transaction_type == "income", Transaction.amount),
                            else_=Decimal("0")
                        )
                    ).label("income"),
                    func.sum(
                        func.case(
                            (Transaction.transaction_type == "expense", Transaction.amount),
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
                        Transaction.is_excluded == False,
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
            result = await self.db.execute(
                select(
                    Transaction.transaction_date,
                    func.sum(
                        func.case(
                            (Transaction.transaction_type == "income", Transaction.amount),
                            else_=Decimal("0")
                        )
                    ).label("income"),
                    func.sum(
                        func.case(
                            (Transaction.transaction_type == "expense", Transaction.amount),
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
                        Transaction.is_excluded == False,
                    )
                )
                .group_by(Transaction.transaction_date)
                .order_by(Transaction.transaction_date)
            )
        
        rows = result.all()
        
        data_points = []
        total_spending = Decimal("0")
        
        for row in rows:
            if period == "monthly":
                period_str = f"{int(row.year)}-{int(row.month):02d}"
            else:
                period_str = row.transaction_date.isoformat()
            
            income = row.income or Decimal("0")
            expenses = row.expenses or Decimal("0")
            total_spending += expenses
            
            data_points.append(TrendDataPoint(
                period=period_str,
                income=income,
                expenses=expenses,
                net=income - expenses,
                transaction_count=row.count,
            ))
        
        # Determine trend
        if len(data_points) >= 2:
            first_half = sum(dp.expenses for dp in data_points[:len(data_points)//2])
            second_half = sum(dp.expenses for dp in data_points[len(data_points)//2:])
            
            if second_half > first_half * Decimal("1.1"):
                overall_trend = "increasing"
            elif second_half < first_half * Decimal("0.9"):
                overall_trend = "decreasing"
            else:
                overall_trend = "stable"
        else:
            overall_trend = "stable"
        
        avg_spending = Decimal("0")
        if data_points:
            avg_spending = total_spending / len(data_points)
        
        return TrendData(
            aggregation=period,
            data_points=data_points,
            overall_trend=overall_trend,
            average_spending=avg_spending,
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
            generated_at=now.isoformat(),
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
        spending = await self.get_category_breakdown(user_id, month_start, today)
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
                    Transaction.transaction_type == "expense",
                    Transaction.merchant_name != None,
                    Transaction.is_excluded == False,
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
