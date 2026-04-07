/**
 * Type definitions for the Finance Tracker API
 */

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  phone: string | null;
  avatar_url: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login: string | null;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  icon: string | null;
  color: string | null;
  category_type: "expense" | "income" | "both";
}

export interface Transaction {
  id: string;
  amount: number;
  currency: string;
  transaction_date: string;
  description: string;
  merchant_name: string | null;
  merchant_category: string | null;
  transaction_type: "expense" | "income" | "transfer";
  category: Category | null;
  is_auto_categorized: boolean;
  categorization_confidence: number | null;
  source: string | null;
  notes: string | null;
  tags: string | null;
  is_recurring: boolean;
  is_excluded: boolean;
  created_at: string;
  updated_at: string;
}

export interface TransactionListResponse {
  items: Transaction[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface SpendingSummary {
  period_start: string;
  period_end: string;
  total_income: number;
  total_expenses: number;
  net_savings: number;
  savings_rate: number;
  transaction_count: number;
  average_transaction: number;
  largest_expense: number | null;
  largest_income: number | null;
}

export interface CategorySpending {
  category_id: string;
  category_name: string;
  category_icon: string | null;
  category_color: string | null;
  amount: number;
  percentage: number;
  transaction_count: number;
  average_transaction: number;
}

export interface CategoryBreakdown {
  period_start: string;
  period_end: string;
  total_amount: number;
  categories: CategorySpending[];
  uncategorized_amount: number;
  uncategorized_count: number;
}

export interface TrendDataPoint {
  period: string;
  income: number;
  expenses: number;
  net: number;
  transaction_count: number;
}

export interface TrendData {
  aggregation: string;
  data_points: TrendDataPoint[];
  overall_trend: "increasing" | "decreasing" | "stable";
  average_spending: number;
}

export interface Insight {
  id: string;
  type: "spending" | "saving" | "anomaly" | "recommendation";
  severity: "info" | "warning" | "alert";
  title: string;
  description: string;
  action: string | null;
  data: Record<string, unknown> | null;
  created_at: string;
}

export interface BudgetCategoryStatus {
  budget_id: string;
  category_id: string | null;
  category_name: string;
  budget_amount: number;
  spent_amount: number;
  remaining_amount: number;
  utilization_percentage: number;
  is_over_budget: boolean;
  projected_end_of_month: number;
  days_remaining: number;
}

export interface BudgetStatus {
  period: string;
  period_start: string;
  period_end: string;
  total_budget: number;
  total_spent: number;
  total_remaining: number;
  overall_utilization: number;
  categories: BudgetCategoryStatus[];
  alerts: string[];
}
