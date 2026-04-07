"use client";

import { useState, useEffect } from "react";
import {
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import { TrendingUp, TrendingDown, AlertCircle, Lightbulb, IndianRupee } from "lucide-react";
import { analyticsApi } from "@/lib/api";

// Category colors for consistent visualization
const CATEGORY_COLORS: Record<string, string> = {
  "Food & Dining": "#ef4444",
  "Transport": "#22c55e",
  "Shopping": "#8b5cf6",
  "Utilities": "#f59e0b",
  "Entertainment": "#ec4899",
  "Healthcare": "#06b6d4",
  "Housing": "#3b82f6",
  "Education": "#84cc16",
  "Financial": "#14b8a6",
  "Personal": "#6b7280",
};

// Sample data - would come from API
const monthlyTrendData = [
  { month: "Oct", income: 75000, expenses: 48000, savings: 27000 },
  { month: "Nov", income: 75000, expenses: 52000, savings: 23000 },
  { month: "Dec", income: 82000, expenses: 61000, savings: 21000 },
  { month: "Jan", income: 75000, expenses: 49000, savings: 26000 },
  { month: "Feb", income: 78000, expenses: 51000, savings: 27000 },
  { month: "Mar", income: 75000, expenses: 47000, savings: 28000 },
];

const categoryData = [
  { name: "Food & Dining", value: 12500, percentage: 26.6 },
  { name: "Transport", value: 6200, percentage: 13.2 },
  { name: "Shopping", value: 8500, percentage: 18.1 },
  { name: "Utilities", value: 4800, percentage: 10.2 },
  { name: "Entertainment", value: 3200, percentage: 6.8 },
  { name: "Healthcare", value: 2800, percentage: 6.0 },
  { name: "Housing", value: 15000, percentage: 31.9 },
];

const detailedBreakdown = [
  {
    category: "Transport",
    total: 6200,
    change: 12,
    subcategories: [
      { name: "Petrol", amount: 4200, merchant: "Indian Oil, HP, BPCL" },
      { name: "Cab/Auto", amount: 1500, merchant: "Uber, Ola" },
      { name: "Parking", amount: 500, merchant: "Various" },
    ],
  },
  {
    category: "Food & Dining",
    total: 12500,
    change: -8,
    subcategories: [
      { name: "Groceries/Ration", amount: 6000, merchant: "BigBasket, DMart" },
      { name: "Fast Food", amount: 3500, merchant: "Swiggy, Zomato" },
      { name: "Restaurants", amount: 2500, merchant: "Various" },
      { name: "Coffee/Beverages", amount: 500, merchant: "Starbucks, CCD" },
    ],
  },
  {
    category: "Utilities",
    total: 4800,
    change: 5,
    subcategories: [
      { name: "Electricity", amount: 2200, merchant: "State EB" },
      { name: "Internet", amount: 999, merchant: "Jio Fiber" },
      { name: "Mobile", amount: 799, merchant: "Airtel" },
      { name: "Gas", amount: 800, merchant: "Indane" },
    ],
  },
  {
    category: "Shopping",
    total: 8500,
    change: 22,
    subcategories: [
      { name: "Clothes", amount: 4500, merchant: "Amazon, Myntra" },
      { name: "Electronics", amount: 2500, merchant: "Flipkart" },
      { name: "Domestic Accessories", amount: 1500, merchant: "Amazon, Local" },
    ],
  },
];

const insights: Array<{
  type: "warning" | "info" | "success";
  title: string;
  message: string;
  suggestion: string;
}> = [
  {
    type: "warning",
    title: "Petrol Spending High",
    message: "You spend ₹4,200/month on petrol - 68% more than average users in your category.",
    suggestion: "Consider carpooling or public transport for some trips.",
  },
  {
    type: "info",
    title: "Fast Food Pattern",
    message: "You spend more on fast food during weekends (avg ₹800 vs ₹400 weekdays).",
    suggestion: "Plan home-cooked meals for weekends to save ₹1,600/month.",
  },
  {
    type: "success",
    title: "Groceries Under Control",
    message: "Your grocery spending (₹6,000) is 20% below average for your profile.",
    suggestion: "Great job! Keep maintaining this habit.",
  },
  {
    type: "info",
    title: "Subscriptions Audit",
    message: "You have 5 active subscriptions totaling ₹1,499/month.",
    suggestion: "Review Netflix (₹649), Spotify (₹119), Prime (₹299) for usage.",
  },
];

const benchmarkData = [
  { category: "Petrol", yours: 4200, average: 2500, diff: 68 },
  { category: "Groceries", yours: 6000, average: 8000, diff: -25 },
  { category: "Fast Food", yours: 3500, average: 2000, diff: 75 },
  { category: "Utilities", yours: 4800, average: 4500, diff: 7 },
  { category: "Entertainment", yours: 3200, average: 3000, diff: 7 },
];

export function AnalyticsDashboard() {
  const [loading, setLoading] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState("month");

  const totalExpenses = categoryData.reduce((sum, cat) => sum + cat.value, 0);
  const totalIncome = 75000;
  const savings = totalIncome - totalExpenses;
  const savingsRate = ((savings / totalIncome) * 100).toFixed(1);

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <SummaryCard
          title="Total Income"
          value={totalIncome}
          icon={<TrendingUp className="h-4 w-4 text-income" />}
          trend={{ value: 4, positive: true }}
        />
        <SummaryCard
          title="Total Expenses"
          value={totalExpenses}
          icon={<TrendingDown className="h-4 w-4 text-expense" />}
          trend={{ value: 8, positive: false }}
        />
        <SummaryCard
          title="Savings"
          value={savings}
          icon={<IndianRupee className="h-4 w-4 text-primary" />}
          subtitle={`${savingsRate}% savings rate`}
        />
        <SummaryCard
          title="Top Expense"
          value={15000}
          icon={<AlertCircle className="h-4 w-4 text-warning" />}
          subtitle="Housing (Rent)"
        />
      </div>

      {/* Charts Row */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Monthly Trend */}
        <div className="rounded-lg border bg-card p-6">
          <h3 className="mb-4 font-semibold">Income vs Expenses Trend</h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={monthlyTrendData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="month" className="text-xs" />
              <YAxis className="text-xs" tickFormatter={(v) => `₹${v/1000}k`} />
              <Tooltip
                formatter={(value: number) => [`₹${value.toLocaleString()}`, ""]}
                contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}
              />
              <Legend />
              <Line type="monotone" dataKey="income" stroke="#22c55e" strokeWidth={2} name="Income" />
              <Line type="monotone" dataKey="expenses" stroke="#ef4444" strokeWidth={2} name="Expenses" />
              <Line type="monotone" dataKey="savings" stroke="#3b82f6" strokeWidth={2} name="Savings" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Category Pie Chart */}
        <div className="rounded-lg border bg-card p-6">
          <h3 className="mb-4 font-semibold">Spending by Category</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={categoryData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
                label={({ name, percentage }) => `${name}: ${percentage}%`}
                labelLine={false}
              >
                {categoryData.map((entry, index) => (
                  <Cell key={entry.name} fill={CATEGORY_COLORS[entry.name] || "#6b7280"} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => [`₹${value.toLocaleString()}`, "Amount"]} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed Category Breakdown - CA Level */}
      <div className="rounded-lg border bg-card p-6">
        <h3 className="mb-4 font-semibold">Detailed Category Breakdown</h3>
        <div className="space-y-6">
          {detailedBreakdown.map((category) => (
            <div key={category.category} className="border-b pb-4 last:border-0">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: CATEGORY_COLORS[category.category] || "#6b7280" }}
                  />
                  <span className="font-medium">{category.category}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="font-semibold">₹{category.total.toLocaleString()}</span>
                  <span className={`text-sm flex items-center gap-1 ${category.change > 0 ? "text-expense" : "text-income"}`}>
                    {category.change > 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                    {Math.abs(category.change)}%
                  </span>
                </div>
              </div>
              <div className="ml-5 space-y-1">
                {category.subcategories.map((sub) => (
                  <div key={sub.name} className="flex justify-between text-sm text-muted-foreground">
                    <span>├── {sub.name}</span>
                    <div className="flex gap-4">
                      <span className="text-foreground">₹{sub.amount.toLocaleString()}</span>
                      <span className="text-xs">{sub.merchant}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Insights */}
      <div className="rounded-lg border bg-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Lightbulb className="h-5 w-5 text-warning" />
          <h3 className="font-semibold">AI-Powered Insights</h3>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {insights.map((insight, index) => (
            <InsightCard key={index} {...insight} />
          ))}
        </div>
      </div>

      {/* Benchmark Comparison */}
      <div className="rounded-lg border bg-card p-6">
        <h3 className="mb-4 font-semibold">Benchmark Comparison (vs Average User)</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b text-left text-sm text-muted-foreground">
                <th className="pb-3 font-medium">Category</th>
                <th className="pb-3 font-medium text-right">Your Spending</th>
                <th className="pb-3 font-medium text-right">Average</th>
                <th className="pb-3 font-medium text-right">Difference</th>
              </tr>
            </thead>
            <tbody>
              {benchmarkData.map((row) => (
                <tr key={row.category} className="border-b last:border-0">
                  <td className="py-3 font-medium">{row.category}</td>
                  <td className="py-3 text-right">₹{row.yours.toLocaleString()}</td>
                  <td className="py-3 text-right text-muted-foreground">₹{row.average.toLocaleString()}</td>
                  <td className={`py-3 text-right font-medium ${row.diff > 0 ? "text-expense" : "text-income"}`}>
                    {row.diff > 0 ? "+" : ""}{row.diff}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Budget Progress */}
      <div className="rounded-lg border bg-card p-6">
        <h3 className="mb-4 font-semibold">Budget Status</h3>
        <div className="space-y-4">
          <BudgetProgress category="Groceries" spent={6000} budget={8000} />
          <BudgetProgress category="Fast Food" spent={3500} budget={3000} />
          <BudgetProgress category="Entertainment" spent={3200} budget={4000} />
          <BudgetProgress category="Transportation" spent={6200} budget={7000} />
          <BudgetProgress category="Utilities" spent={4800} budget={5000} />
        </div>
      </div>
    </div>
  );
}

function SummaryCard({
  title,
  value,
  icon,
  trend,
  subtitle,
}: {
  title: string;
  value: number;
  icon: React.ReactNode;
  trend?: { value: number; positive: boolean };
  subtitle?: string;
}) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">{title}</span>
        {icon}
      </div>
      <div className="mt-2 text-2xl font-bold">₹{value.toLocaleString()}</div>
      {trend && (
        <div className={`mt-1 text-xs ${trend.positive ? "text-income" : "text-expense"}`}>
          {trend.positive ? "↑" : "↓"} {trend.value}% from last month
        </div>
      )}
      {subtitle && <div className="mt-1 text-xs text-muted-foreground">{subtitle}</div>}
    </div>
  );
}

function InsightCard({
  type,
  title,
  message,
  suggestion,
}: {
  type: "warning" | "info" | "success";
  title: string;
  message: string;
  suggestion: string;
}) {
  const colors = {
    warning: "border-l-warning bg-warning/5",
    info: "border-l-primary bg-primary/5",
    success: "border-l-income bg-income/5",
  };

  return (
    <div className={`rounded-lg border-l-4 p-4 ${colors[type]}`}>
      <h4 className="font-medium">{title}</h4>
      <p className="mt-1 text-sm text-muted-foreground">{message}</p>
      <p className="mt-2 text-sm font-medium text-primary">💡 {suggestion}</p>
    </div>
  );
}

function BudgetProgress({
  category,
  spent,
  budget,
}: {
  category: string;
  spent: number;
  budget: number;
}) {
  const percentage = (spent / budget) * 100;
  const isOver = percentage > 100;
  const isWarning = percentage > 80 && percentage <= 100;

  return (
    <div>
      <div className="flex justify-between text-sm">
        <span className="font-medium">{category}</span>
        <span className={isOver ? "text-expense font-medium" : isWarning ? "text-warning" : "text-muted-foreground"}>
          ₹{spent.toLocaleString()} / ₹{budget.toLocaleString()}
        </span>
      </div>
      <div className="mt-2 h-2 rounded-full bg-muted">
        <div
          className={`h-full rounded-full transition-all ${
            isOver ? "bg-expense" : isWarning ? "bg-warning" : "bg-income"
          }`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
      {isOver && (
        <p className="mt-1 text-xs text-expense">
          Over budget by ₹{(spent - budget).toLocaleString()}
        </p>
      )}
    </div>
  );
}


