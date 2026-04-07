"""
Financial Insights Engine.

This module generates CA-level financial insights and analytics
for personal finance management.

Features:
- Monthly and yearly summaries
- Category-wise spending analysis
- Trend detection and comparisons
- Smart spending insights
- Benchmark comparisons against user profiles
- Savings recommendations
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from collections import defaultdict
from uuid import uuid4
import calendar

from app.ml.categories import (
    CATEGORY_HIERARCHY,
    INDIAN_AVERAGE_SPENDING,
    SUBCATEGORY_BENCHMARKS,
    get_benchmark_for_user_type,
    get_recommended_budget,
    CategoryType,
)

logger = logging.getLogger(__name__)


class TrendDirection(str, Enum):
    """Direction of a trend."""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"
    INCREASING = "increasing"
    DECREASING = "decreasing"


class InsightType(str, Enum):
    """Type of insight generated."""
    SPENDING_PATTERN = "spending_pattern"
    SPENDING = "spending"
    SAVING = "saving"
    ANOMALY = "anomaly"
    SAVING_OPPORTUNITY = "saving_opportunity"
    RECURRING_DETECTION = "recurring_detection"
    CATEGORY_ALERT = "category_alert"
    GOAL_PROGRESS = "goal_progress"
    BENCHMARK_COMPARISON = "benchmark_comparison"
    TIME_PATTERN = "time_pattern"
    SUBSCRIPTION_ALERT = "subscription_alert"
    RECOMMENDATION = "recommendation"


class InsightSeverity(str, Enum):
    """Severity/importance of an insight."""
    INFO = "info"
    TIP = "tip"
    WARNING = "warning"
    ALERT = "alert"


@dataclass
class InsightData:
    """A single financial insight (new format)."""
    type: InsightType
    severity: InsightSeverity
    title: str
    message: str
    category: Optional[str] = None
    amount: Optional[float] = None
    percentage_change: Optional[float] = None
    trend: Optional[TrendDirection] = None
    action_suggested: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "category": self.category,
            "amount": self.amount,
            "percentage_change": self.percentage_change,
            "trend": self.trend.value if self.trend else None,
            "action_suggested": self.action_suggested,
            "metadata": self.metadata,
        }


@dataclass
class CategoryBreakdownData:
    """Breakdown of spending in a category."""
    category: str
    subcategory: Optional[str]
    amount: float
    transaction_count: int
    percentage_of_total: float
    average_transaction: float
    trend: TrendDirection
    change_from_last_period: float  # percentage
    benchmark_difference: Optional[float] = None  # vs benchmark
    subcategory_breakdown: List["CategoryBreakdownData"] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category,
            "subcategory": self.subcategory,
            "amount": round(self.amount, 2),
            "transaction_count": self.transaction_count,
            "percentage_of_total": round(self.percentage_of_total, 2),
            "average_transaction": round(self.average_transaction, 2),
            "trend": self.trend.value,
            "change_from_last_period": round(self.change_from_last_period, 2),
            "benchmark_difference": round(self.benchmark_difference, 2) if self.benchmark_difference else None,
            "subcategory_breakdown": [s.to_dict() for s in self.subcategory_breakdown],
        }


@dataclass
class MonthlyInsights:
    """Complete monthly financial summary."""
    month: int
    year: int
    total_income: float
    total_expenses: float
    net_savings: float
    savings_rate: float  # percentage
    expense_categories: List[CategoryBreakdownData]
    income_categories: List[CategoryBreakdownData]
    top_spending_category: Optional[CategoryBreakdownData]
    insights: List[InsightData]
    comparison_to_last_month: Dict[str, float]  # category -> change %
    daily_average_spending: float
    transaction_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "month": self.month,
            "year": self.year,
            "total_income": round(self.total_income, 2),
            "total_expenses": round(self.total_expenses, 2),
            "net_savings": round(self.net_savings, 2),
            "savings_rate": round(self.savings_rate, 2),
            "expense_categories": [c.to_dict() for c in self.expense_categories],
            "income_categories": [c.to_dict() for c in self.income_categories],
            "top_spending_category": self.top_spending_category.to_dict() if self.top_spending_category else None,
            "insights": [i.to_dict() for i in self.insights],
            "comparison_to_last_month": {
                k: round(v, 2) for k, v in self.comparison_to_last_month.items()
            },
            "daily_average_spending": round(self.daily_average_spending, 2),
            "transaction_count": self.transaction_count,
        }


@dataclass
class BenchmarkResult:
    """Result of benchmark comparison."""
    user_type: str
    total_spending: float
    benchmark_spending: float
    overall_difference: float  # percentage
    category_comparisons: List[Dict[str, Any]]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_type": self.user_type,
            "total_spending": round(self.total_spending, 2),
            "benchmark_spending": round(self.benchmark_spending, 2),
            "overall_difference": round(self.overall_difference, 2),
            "category_comparisons": self.category_comparisons,
            "recommendations": self.recommendations,
        }


@dataclass
class Transaction:
    """Transaction data for analysis."""
    id: str
    amount: float
    category: str
    subcategory: str
    date: datetime
    description: str
    transaction_type: str  # 'credit' or 'debit'
    merchant_name: Optional[str] = None
    is_recurring: bool = False


class InsightsEngine:
    """
    Engine for generating financial insights and analytics.
    
    Provides CA-level analysis including:
    - Monthly and yearly summaries
    - Category-wise breakdowns
    - Trend analysis
    - Smart insights and recommendations
    - Benchmark comparisons
    """
    
    def __init__(self, user_type: str = "professional"):
        """
        Initialize the insights engine.
        
        Args:
            user_type: User profile type for benchmarking
        """
        self.user_type = user_type
        self.benchmarks = INDIAN_AVERAGE_SPENDING.get(user_type, {})
    
    # =========================================================================
    # LEGACY API - For backward compatibility with existing schemas
    # =========================================================================
    
    def generate_insights(
        self,
        summary,  # SpendingSummary from schemas
        trends,   # TrendData from schemas
        categories,  # CategoryBreakdown from schemas
    ) -> List:
        """
        Generate insights from financial data (legacy API).
        
        Args:
            summary: Spending summary data
            trends: Trend data
            categories: Category breakdown
            
        Returns:
            List of generated insights (Insight schema format)
        """
        # Import here to avoid circular imports
        try:
            from app.schemas.analytics import Insight
        except ImportError:
            # If schema not available, return basic dict format
            Insight = None
        
        insights = []
        now = datetime.utcnow().isoformat()
        
        # Insight 1: Savings rate
        if summary.savings_rate < 20:
            insight_data = {
                "id": str(uuid4()),
                "type": "saving",
                "severity": "warning",
                "title": "Low Savings Rate",
                "description": f"Your savings rate is {summary.savings_rate:.1f}%. "
                              "Financial experts recommend saving at least 20% of your income.",
                "action": "Consider reviewing your expenses and identifying areas to cut back.",
                "data": {"savings_rate": summary.savings_rate},
                "created_at": now,
            }
            if Insight:
                insights.append(Insight(**insight_data))
            else:
                insights.append(insight_data)
        elif summary.savings_rate >= 30:
            insight_data = {
                "id": str(uuid4()),
                "type": "saving",
                "severity": "info",
                "title": "Great Savings Rate!",
                "description": f"Your savings rate of {summary.savings_rate:.1f}% is excellent! "
                              "Keep up the good work.",
                "action": None,
                "data": {"savings_rate": summary.savings_rate},
                "created_at": now,
            }
            if Insight:
                insights.append(Insight(**insight_data))
            else:
                insights.append(insight_data)
        
        # Insight 2: Spending trend
        if trends.overall_trend == "increasing":
            insight_data = {
                "id": str(uuid4()),
                "type": "spending",
                "severity": "warning",
                "title": "Rising Spending Trend",
                "description": "Your spending has been increasing over the past months. "
                              "This may impact your savings goals.",
                "action": "Review recent transactions to identify what's driving the increase.",
                "data": {"trend": "increasing"},
                "created_at": now,
            }
            if Insight:
                insights.append(Insight(**insight_data))
            else:
                insights.append(insight_data)
        elif trends.overall_trend == "decreasing":
            insight_data = {
                "id": str(uuid4()),
                "type": "spending",
                "severity": "info",
                "title": "Declining Spending Trend",
                "description": "Great job! Your spending has been decreasing recently.",
                "action": None,
                "data": {"trend": "decreasing"},
                "created_at": now,
            }
            if Insight:
                insights.append(Insight(**insight_data))
            else:
                insights.append(insight_data)
        
        # Insight 3: Top spending category
        if categories.categories:
            top_category = categories.categories[0]
            if top_category.percentage > 40:
                insight_data = {
                    "id": str(uuid4()),
                    "type": "spending",
                    "severity": "alert",
                    "title": f"High {top_category.category_name} Spending",
                    "description": f"{top_category.category_name} accounts for "
                                  f"{top_category.percentage:.1f}% of your spending. "
                                  "This is significantly above average.",
                    "action": f"Look for ways to reduce {top_category.category_name.lower()} expenses.",
                    "data": {
                        "category": top_category.category_name,
                        "percentage": top_category.percentage,
                        "amount": float(top_category.amount),
                    },
                    "created_at": now,
                }
                if Insight:
                    insights.append(Insight(**insight_data))
                else:
                    insights.append(insight_data)
        
        # Insight 4: Uncategorized transactions
        if categories.uncategorized_count > 5:
            percentage = 0
            if categories.total_amount > 0:
                percentage = float(categories.uncategorized_amount / categories.total_amount * 100)
            
            insight_data = {
                "id": str(uuid4()),
                "type": "recommendation",
                "severity": "info",
                "title": "Uncategorized Transactions",
                "description": f"You have {categories.uncategorized_count} uncategorized transactions "
                              f"({percentage:.1f}% of spending). Categorizing them will improve your insights.",
                "action": "Review and categorize your recent transactions.",
                "data": {
                    "count": categories.uncategorized_count,
                    "amount": float(categories.uncategorized_amount),
                },
                "created_at": now,
            }
            if Insight:
                insights.append(Insight(**insight_data))
            else:
                insights.append(insight_data)
        
        # Insight 5: Large transactions
        if summary.largest_expense and summary.average_transaction:
            if summary.largest_expense > summary.average_transaction * 5:
                insight_data = {
                    "id": str(uuid4()),
                    "type": "anomaly",
                    "severity": "info",
                    "title": "Large Expense Detected",
                    "description": f"Your largest expense (₹{summary.largest_expense:,.2f}) is "
                                  "significantly higher than your average transaction.",
                    "action": "Verify this transaction is correct and expected.",
                    "data": {"largest_expense": float(summary.largest_expense)},
                    "created_at": now,
                }
                if Insight:
                    insights.append(Insight(**insight_data))
                else:
                    insights.append(insight_data)
        
        # Insight 6: Spending consistency
        if trends.data_points:
            amounts = [dp.expenses for dp in trends.data_points if dp.expenses]
            if amounts:
                avg = sum(amounts) / len(amounts)
                variance = sum((x - avg) ** 2 for x in amounts) / len(amounts) if len(amounts) > 1 else 0
                
                if variance > avg * 0.5:  # High variance
                    insight_data = {
                        "id": str(uuid4()),
                        "type": "spending",
                        "severity": "info",
                        "title": "Inconsistent Spending Pattern",
                        "description": "Your spending varies significantly from month to month. "
                                      "Consistent spending can help with budgeting.",
                        "action": "Consider setting a monthly spending limit to smooth out variations.",
                        "data": {"average": float(avg)},
                        "created_at": now,
                    }
                    if Insight:
                        insights.append(Insight(**insight_data))
                    else:
                        insights.append(insight_data)
        
        return insights
    
    # =========================================================================
    # NEW API - Full-featured insights generation
    # =========================================================================
    
    def generate_monthly_summary(
        self,
        transactions: List[Transaction],
        month: int,
        year: int,
        previous_month_transactions: Optional[List[Transaction]] = None
    ) -> MonthlyInsights:
        """
        Generate comprehensive monthly financial summary.
        
        Args:
            transactions: Transactions for the month
            month: Month number (1-12)
            year: Year
            previous_month_transactions: Optional transactions from previous month
            
        Returns:
            MonthlyInsights with complete analysis
        """
        # Separate income and expenses
        expenses = [t for t in transactions if t.transaction_type == 'debit']
        income = [t for t in transactions if t.transaction_type == 'credit']
        
        total_income = sum(t.amount for t in income)
        total_expenses = sum(t.amount for t in expenses)
        net_savings = total_income - total_expenses
        savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0
        
        # Calculate days in month for daily average
        days_in_month = calendar.monthrange(year, month)[1]
        daily_average = total_expenses / days_in_month if days_in_month > 0 else 0
        
        # Generate category breakdowns
        expense_categories = self._generate_category_breakdown(
            expenses, total_expenses, previous_month_transactions
        )
        income_categories = self._generate_category_breakdown(
            income, total_income, None
        )
        
        # Find top spending category
        top_spending = max(expense_categories, key=lambda x: x.amount) if expense_categories else None
        
        # Calculate comparison to last month
        comparison = {}
        if previous_month_transactions:
            prev_category_totals = self._get_category_totals(
                [t for t in previous_month_transactions if t.transaction_type == 'debit']
            )
            curr_category_totals = self._get_category_totals(expenses)
            
            for category in set(list(prev_category_totals.keys()) + list(curr_category_totals.keys())):
                prev_amt = prev_category_totals.get(category, 0)
                curr_amt = curr_category_totals.get(category, 0)
                if prev_amt > 0:
                    change = ((curr_amt - prev_amt) / prev_amt) * 100
                elif curr_amt > 0:
                    change = 100  # New category
                else:
                    change = 0
                comparison[category] = change
        
        # Generate insights
        insights = self._generate_monthly_insights(
            transactions, expense_categories, income_categories,
            total_income, total_expenses, savings_rate, comparison
        )
        
        return MonthlyInsights(
            month=month,
            year=year,
            total_income=total_income,
            total_expenses=total_expenses,
            net_savings=net_savings,
            savings_rate=savings_rate,
            expense_categories=expense_categories,
            income_categories=income_categories,
            top_spending_category=top_spending,
            insights=insights,
            comparison_to_last_month=comparison,
            daily_average_spending=daily_average,
            transaction_count=len(transactions),
        )
    
    def generate_category_analysis(
        self,
        transactions: List[Transaction],
        period_months: int = 3
    ) -> List[CategoryBreakdownData]:
        """
        Generate detailed category-wise analysis.
        
        Args:
            transactions: List of transactions to analyze
            period_months: Number of months to analyze
            
        Returns:
            List of CategoryBreakdownData with detailed analysis
        """
        expenses = [t for t in transactions if t.transaction_type == 'debit']
        total = sum(t.amount for t in expenses)
        
        # Group by category
        category_data: Dict[str, List[Transaction]] = defaultdict(list)
        for t in expenses:
            category_data[t.category].append(t)
        
        breakdowns = []
        for category, cat_transactions in category_data.items():
            cat_total = sum(t.amount for t in cat_transactions)
            
            # Get subcategory breakdown
            subcategory_data: Dict[str, List[Transaction]] = defaultdict(list)
            for t in cat_transactions:
                subcategory_data[t.subcategory].append(t)
            
            subcategory_breakdowns = []
            for subcategory, sub_transactions in subcategory_data.items():
                sub_total = sum(t.amount for t in sub_transactions)
                
                # Get benchmark
                benchmark = get_benchmark_for_user_type(
                    self.user_type, subcategory=subcategory
                )
                monthly_avg = sub_total / period_months
                benchmark_diff = None
                if benchmark:
                    benchmark_diff = ((monthly_avg - benchmark) / benchmark) * 100
                
                subcategory_breakdowns.append(CategoryBreakdownData(
                    category=category,
                    subcategory=subcategory,
                    amount=sub_total,
                    transaction_count=len(sub_transactions),
                    percentage_of_total=(sub_total / cat_total * 100) if cat_total > 0 else 0,
                    average_transaction=sub_total / len(sub_transactions) if sub_transactions else 0,
                    trend=self._calculate_trend(sub_transactions),
                    change_from_last_period=0,  # Would need historical data
                    benchmark_difference=benchmark_diff,
                ))
            
            # Sort subcategories by amount
            subcategory_breakdowns.sort(key=lambda x: x.amount, reverse=True)
            
            # Get category benchmark
            cat_benchmark = get_benchmark_for_user_type(self.user_type, category=category)
            monthly_cat_avg = cat_total / period_months
            cat_benchmark_diff = None
            if cat_benchmark:
                cat_benchmark_diff = ((monthly_cat_avg - cat_benchmark) / cat_benchmark) * 100
            
            breakdowns.append(CategoryBreakdownData(
                category=category,
                subcategory=None,
                amount=cat_total,
                transaction_count=len(cat_transactions),
                percentage_of_total=(cat_total / total * 100) if total > 0 else 0,
                average_transaction=cat_total / len(cat_transactions) if cat_transactions else 0,
                trend=self._calculate_trend(cat_transactions),
                change_from_last_period=0,
                benchmark_difference=cat_benchmark_diff,
                subcategory_breakdown=subcategory_breakdowns,
            ))
        
        # Sort by amount
        breakdowns.sort(key=lambda x: x.amount, reverse=True)
        return breakdowns
    
    def generate_spending_insights(
        self,
        transactions: List[Transaction],
        historical_transactions: Optional[List[Transaction]] = None
    ) -> List[InsightData]:
        """
        Generate smart spending insights.
        
        Args:
            transactions: Recent transactions
            historical_transactions: Historical transactions for comparison
            
        Returns:
            List of insights
        """
        insights: List[InsightData] = []
        
        expenses = [t for t in transactions if t.transaction_type == 'debit']
        
        # 1. Weekend vs Weekday Analysis
        weekend_expenses = [t for t in expenses if t.date.weekday() >= 5]
        weekday_expenses = [t for t in expenses if t.date.weekday() < 5]
        
        if weekend_expenses and weekday_expenses:
            weekend_daily = sum(t.amount for t in weekend_expenses) / max(1, len(set(t.date.date() for t in weekend_expenses)))
            weekday_daily = sum(t.amount for t in weekday_expenses) / max(1, len(set(t.date.date() for t in weekday_expenses)))
            
            if weekend_daily > weekday_daily * 1.5:
                insights.append(InsightData(
                    type=InsightType.TIME_PATTERN,
                    severity=InsightSeverity.TIP,
                    title="Weekend Spending Pattern",
                    message=f"You spend more on weekends (avg ₹{weekend_daily:,.0f}/day) compared to weekdays (₹{weekday_daily:,.0f}/day)",
                    amount=weekend_daily - weekday_daily,
                    trend=TrendDirection.UP,
                    action_suggested="Consider setting a weekend spending budget",
                ))
        
        # 2. Subscription Detection
        subscriptions = [t for t in expenses if self._looks_like_subscription(t)]
        if subscriptions:
            sub_total = sum(t.amount for t in subscriptions)
            unique_subs = list(set(t.merchant_name for t in subscriptions if t.merchant_name))
            insights.append(InsightData(
                type=InsightType.SUBSCRIPTION_ALERT,
                severity=InsightSeverity.INFO,
                title="Active Subscriptions",
                message=f"You have {len(unique_subs)} active subscriptions totaling ₹{sub_total:,.0f}/month",
                amount=sub_total,
                metadata={"subscriptions": unique_subs},
            ))
        
        # 3. High Spending Categories
        category_totals = self._get_category_totals(expenses)
        for category, total in category_totals.items():
            benchmark = get_benchmark_for_user_type(self.user_type, category=category)
            if benchmark and total > benchmark * 1.5:
                diff_pct = ((total - benchmark) / benchmark) * 100
                insights.append(InsightData(
                    type=InsightType.CATEGORY_ALERT,
                    severity=InsightSeverity.WARNING,
                    title=f"High {category} Spending",
                    message=f"Your {category} spending (₹{total:,.0f}) is {diff_pct:.0f}% above average",
                    category=category,
                    amount=total,
                    percentage_change=diff_pct,
                    trend=TrendDirection.UP,
                    action_suggested=f"Review your {category.lower()} expenses for savings",
                ))
        
        # 4. Food Delivery vs Groceries comparison
        food_delivery = sum(
            t.amount for t in expenses 
            if t.subcategory in ['Food Delivery', 'Fast Food']
        )
        groceries = sum(
            t.amount for t in expenses 
            if t.subcategory in ['Groceries', 'Ration', 'Vegetables/Fruits']
        )
        
        if food_delivery > groceries * 0.5 and groceries > 0:
            insights.append(InsightData(
                type=InsightType.SAVING_OPPORTUNITY,
                severity=InsightSeverity.TIP,
                title="Food Spending Pattern",
                message=f"Your food delivery spending (₹{food_delivery:,.0f}) is {(food_delivery/groceries*100):.0f}% of your grocery spending. Cooking more at home could save money.",
                category="Food & Dining",
                amount=food_delivery,
                action_suggested="Try meal prepping to reduce food delivery orders",
            ))
        
        # 5. Recurring expense detection
        recurring = self._detect_recurring_patterns(expenses)
        for pattern in recurring[:3]:  # Top 3 recurring patterns
            insights.append(InsightData(
                type=InsightType.RECURRING_DETECTION,
                severity=InsightSeverity.INFO,
                title=f"Recurring: {pattern['merchant'] or pattern['category']}",
                message=f"Detected recurring expense: ₹{pattern['amount']:,.0f} around {pattern['day']}th of each month",
                category=pattern['category'],
                amount=pattern['amount'],
                metadata=pattern,
            ))
        
        # 6. Coffee/Beverage spending insight
        coffee_spending = sum(
            t.amount for t in expenses
            if t.subcategory in ['Coffee/Tea', 'Beverages'] or 
            (t.merchant_name and 'coffee' in t.merchant_name.lower())
        )
        
        utility_spending = sum(
            t.amount for t in expenses if t.category == 'Utilities'
        )
        
        if coffee_spending > 0 and utility_spending > 0 and coffee_spending > utility_spending * 0.3:
            insights.append(InsightData(
                type=InsightType.SPENDING_PATTERN,
                severity=InsightSeverity.TIP,
                title="Coffee Spending",
                message=f"Your coffee/beverage spending (₹{coffee_spending:,.0f}) is significant. Consider: That's ₹{coffee_spending*12:,.0f}/year!",
                category="Food & Dining",
                amount=coffee_spending,
                action_suggested="Try brewing at home some days to save",
            ))
        
        # 7. Potential savings based on benchmark
        total_expenses = sum(t.amount for t in expenses)
        benchmark_total = sum(self.benchmarks.values())
        
        if benchmark_total > 0 and total_expenses > benchmark_total * 1.2:
            potential_savings = total_expenses - benchmark_total
            insights.append(InsightData(
                type=InsightType.SAVING_OPPORTUNITY,
                severity=InsightSeverity.TIP,
                title="Potential Savings",
                message=f"Based on your profile, you could potentially save ₹{potential_savings:,.0f}/month by optimizing spending",
                amount=potential_savings,
                action_suggested="Review categories where you exceed benchmarks",
            ))
        
        # Sort by severity (alerts first)
        severity_order = {
            InsightSeverity.ALERT: 0,
            InsightSeverity.WARNING: 1,
            InsightSeverity.TIP: 2,
            InsightSeverity.INFO: 3,
        }
        insights.sort(key=lambda x: severity_order[x.severity])
        
        return insights
    
    def benchmark_comparison(
        self,
        transactions: List[Transaction],
        period_months: int = 1
    ) -> BenchmarkResult:
        """
        Compare user spending against benchmarks.
        
        Args:
            transactions: User's transactions
            period_months: Number of months of data
            
        Returns:
            BenchmarkResult with detailed comparison
        """
        expenses = [t for t in transactions if t.transaction_type == 'debit']
        
        # Get category totals (monthly average)
        category_totals = self._get_category_totals(expenses)
        for cat in category_totals:
            category_totals[cat] /= period_months
        
        total_spending = sum(category_totals.values())
        benchmark_total = sum(self.benchmarks.values())
        
        overall_diff = ((total_spending - benchmark_total) / benchmark_total * 100) if benchmark_total > 0 else 0
        
        # Generate category comparisons
        comparisons = []
        for category, user_amount in category_totals.items():
            benchmark = self.benchmarks.get(category, 0)
            
            if benchmark > 0:
                diff = ((user_amount - benchmark) / benchmark) * 100
                status = "above" if diff > 10 else ("below" if diff < -10 else "on track")
            else:
                diff = 0
                status = "no benchmark"
            
            comparisons.append({
                "category": category,
                "your_spending": round(user_amount, 2),
                "benchmark": benchmark,
                "difference_percent": round(diff, 2),
                "status": status,
            })
        
        # Sort by difference (highest overspending first)
        comparisons.sort(key=lambda x: x["difference_percent"], reverse=True)
        
        # Generate recommendations
        recommendations = []
        for comp in comparisons:
            if comp["difference_percent"] > 30:
                recommendations.append(
                    f"Consider reducing {comp['category']} spending - you're {comp['difference_percent']:.0f}% above benchmark"
                )
            elif comp["difference_percent"] < -30:
                recommendations.append(
                    f"Great job on {comp['category']}! You're saving {abs(comp['difference_percent']):.0f}% compared to average"
                )
        
        if overall_diff > 20:
            recommendations.insert(0, 
                f"Overall spending is {overall_diff:.0f}% above benchmark. Focus on top overspending categories."
            )
        elif overall_diff < -10:
            recommendations.insert(0,
                f"Excellent! You're spending {abs(overall_diff):.0f}% below average. Consider investing the savings."
            )
        
        return BenchmarkResult(
            user_type=self.user_type,
            total_spending=total_spending,
            benchmark_spending=benchmark_total,
            overall_difference=overall_diff,
            category_comparisons=comparisons,
            recommendations=recommendations[:5],  # Top 5 recommendations
        )
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _generate_category_breakdown(
        self,
        transactions: List[Transaction],
        total: float,
        previous_transactions: Optional[List[Transaction]]
    ) -> List[CategoryBreakdownData]:
        """Generate category breakdown from transactions."""
        if not transactions:
            return []
            
        category_data: Dict[str, List[Transaction]] = defaultdict(list)
        for t in transactions:
            category_data[t.category].append(t)
        
        # Get previous period totals for comparison
        prev_totals = {}
        if previous_transactions:
            for t in previous_transactions:
                if t.transaction_type == transactions[0].transaction_type:
                    prev_totals[t.category] = prev_totals.get(t.category, 0) + t.amount
        
        breakdowns = []
        for category, cat_transactions in category_data.items():
            cat_total = sum(t.amount for t in cat_transactions)
            prev_total = prev_totals.get(category, 0)
            
            change = 0
            if prev_total > 0:
                change = ((cat_total - prev_total) / prev_total) * 100
            elif cat_total > 0:
                change = 100
            
            trend = TrendDirection.STABLE
            if change > 10:
                trend = TrendDirection.UP
            elif change < -10:
                trend = TrendDirection.DOWN
            
            breakdowns.append(CategoryBreakdownData(
                category=category,
                subcategory=None,
                amount=cat_total,
                transaction_count=len(cat_transactions),
                percentage_of_total=(cat_total / total * 100) if total > 0 else 0,
                average_transaction=cat_total / len(cat_transactions) if cat_transactions else 0,
                trend=trend,
                change_from_last_period=change,
            ))
        
        breakdowns.sort(key=lambda x: x.amount, reverse=True)
        return breakdowns
    
    def _generate_monthly_insights(
        self,
        transactions: List[Transaction],
        expense_categories: List[CategoryBreakdownData],
        income_categories: List[CategoryBreakdownData],
        total_income: float,
        total_expenses: float,
        savings_rate: float,
        comparison: Dict[str, float]
    ) -> List[InsightData]:
        """Generate insights for monthly summary."""
        insights = []
        
        # Savings rate insight
        if savings_rate >= 30:
            insights.append(InsightData(
                type=InsightType.GOAL_PROGRESS,
                severity=InsightSeverity.INFO,
                title="Great Savings Rate!",
                message=f"You saved {savings_rate:.1f}% of your income this month. Keep it up!",
                percentage_change=savings_rate,
                trend=TrendDirection.UP,
            ))
        elif savings_rate < 10:
            insights.append(InsightData(
                type=InsightType.SAVING_OPPORTUNITY,
                severity=InsightSeverity.WARNING,
                title="Low Savings This Month",
                message=f"Your savings rate is only {savings_rate:.1f}%. Consider reviewing discretionary spending.",
                percentage_change=savings_rate,
                trend=TrendDirection.DOWN,
                action_suggested="Aim for at least 20% savings rate",
            ))
        
        # Categories with significant changes
        for category, change in comparison.items():
            if change > 50:
                insights.append(InsightData(
                    type=InsightType.CATEGORY_ALERT,
                    severity=InsightSeverity.WARNING,
                    title=f"{category} Spending Spike",
                    message=f"Your {category} spending increased by {change:.0f}% from last month",
                    category=category,
                    percentage_change=change,
                    trend=TrendDirection.UP,
                ))
            elif change < -30:
                insights.append(InsightData(
                    type=InsightType.CATEGORY_ALERT,
                    severity=InsightSeverity.INFO,
                    title=f"{category} Spending Reduced",
                    message=f"Great! Your {category} spending decreased by {abs(change):.0f}%",
                    category=category,
                    percentage_change=change,
                    trend=TrendDirection.DOWN,
                ))
        
        # Top spending category insight
        if expense_categories:
            top = expense_categories[0]
            insights.append(InsightData(
                type=InsightType.SPENDING_PATTERN,
                severity=InsightSeverity.INFO,
                title="Top Spending Category",
                message=f"{top.category} was your highest expense at ₹{top.amount:,.0f} ({top.percentage_of_total:.1f}% of total)",
                category=top.category,
                amount=top.amount,
                percentage_change=top.percentage_of_total,
            ))
        
        return insights
    
    def _get_category_totals(self, transactions: List[Transaction]) -> Dict[str, float]:
        """Get total spending per category."""
        totals: Dict[str, float] = defaultdict(float)
        for t in transactions:
            totals[t.category] += t.amount
        return dict(totals)
    
    def _calculate_trend(self, transactions: List[Transaction]) -> TrendDirection:
        """Calculate spending trend from transactions."""
        if len(transactions) < 4:
            return TrendDirection.STABLE
        
        # Sort by date
        sorted_txns = sorted(transactions, key=lambda x: x.date)
        mid = len(sorted_txns) // 2
        
        first_half_avg = sum(t.amount for t in sorted_txns[:mid]) / mid
        second_half_avg = sum(t.amount for t in sorted_txns[mid:]) / (len(sorted_txns) - mid)
        
        if second_half_avg > first_half_avg * 1.15:
            return TrendDirection.UP
        elif second_half_avg < first_half_avg * 0.85:
            return TrendDirection.DOWN
        return TrendDirection.STABLE
    
    def _looks_like_subscription(self, transaction: Transaction) -> bool:
        """Check if transaction looks like a subscription."""
        # Check known subscription merchants
        subscription_keywords = [
            'netflix', 'spotify', 'prime', 'hotstar', 'disney', 'zee5',
            'youtube', 'apple music', 'gaana', 'gym', 'membership',
            'subscription', 'monthly', 'premium',
        ]
        
        description_lower = transaction.description.lower()
        merchant_lower = (transaction.merchant_name or '').lower()
        
        for keyword in subscription_keywords:
            if keyword in description_lower or keyword in merchant_lower:
                return True
        
        # Check typical subscription amounts
        subscription_amounts = [99, 149, 199, 299, 399, 499, 649, 699, 999, 1499]
        if transaction.amount in subscription_amounts:
            return True
        
        return transaction.is_recurring
    
    def _detect_recurring_patterns(
        self,
        transactions: List[Transaction]
    ) -> List[Dict[str, Any]]:
        """Detect recurring transaction patterns."""
        patterns = []
        
        # Group by merchant/category and amount
        groups: Dict[str, List[Transaction]] = defaultdict(list)
        for t in transactions:
            key = f"{t.merchant_name or t.category}:{int(t.amount)}"
            groups[key].append(t)
        
        # Find recurring patterns (same merchant/amount on similar dates)
        for key, txns in groups.items():
            if len(txns) >= 2:
                # Check if transactions occur around similar dates
                days = [t.date.day for t in txns]
                if max(days) - min(days) <= 5:  # Within 5 days range
                    avg_day = sum(days) // len(days)
                    patterns.append({
                        'merchant': txns[0].merchant_name,
                        'category': txns[0].category,
                        'amount': txns[0].amount,
                        'day': avg_day,
                        'occurrences': len(txns),
                    })
        
        # Sort by amount (highest first)
        patterns.sort(key=lambda x: x['amount'], reverse=True)
        return patterns


def format_currency(amount: float, symbol: str = "₹") -> str:
    """Format amount as Indian currency."""
    if amount >= 10000000:  # 1 crore
        return f"{symbol}{amount/10000000:.2f} Cr"
    elif amount >= 100000:  # 1 lakh
        return f"{symbol}{amount/100000:.2f} L"
    elif amount >= 1000:
        return f"{symbol}{amount:,.0f}"
    else:
        return f"{symbol}{amount:.2f}"


def generate_text_summary(insights: MonthlyInsights) -> str:
    """Generate a human-readable text summary."""
    lines = [
        f"📊 Financial Summary - {calendar.month_name[insights.month]} {insights.year}",
        "=" * 50,
        "",
        f"💰 Total Income: {format_currency(insights.total_income)}",
        f"💸 Total Expenses: {format_currency(insights.total_expenses)}",
        f"💵 Net Savings: {format_currency(insights.net_savings)}",
        f"📈 Savings Rate: {insights.savings_rate:.1f}%",
        "",
        "📋 Top Expense Categories:",
    ]
    
    for i, cat in enumerate(insights.expense_categories[:5], 1):
        trend_emoji = "📈" if cat.trend == TrendDirection.UP else ("📉" if cat.trend == TrendDirection.DOWN else "➡️")
        lines.append(
            f"  {i}. {cat.category}: {format_currency(cat.amount)} ({cat.percentage_of_total:.1f}%) {trend_emoji}"
        )
    
    if insights.insights:
        lines.extend(["", "💡 Key Insights:"])
        for insight in insights.insights[:5]:
            emoji = "⚠️" if insight.severity in [InsightSeverity.WARNING, InsightSeverity.ALERT] else "💡"
            lines.append(f"  {emoji} {insight.message}")
    
    return "\n".join(lines)
