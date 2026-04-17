"use client";

import { useMemo, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
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
import {
  TrendingUp,
  TrendingDown,
  AlertCircle,
  Lightbulb,
  IndianRupee,
} from "lucide-react";
import { analyticsApi } from "@/lib/api";
import { formatCurrency, generateColor } from "@/lib/utils";
import { format } from "date-fns";

const focusNames = ["Petrol", "Food", "Utilities", "Clothes", "Groceries"];

export function AnalyticsDashboard() {
  const { data: summary } = useQuery({
    queryKey: ["analytics-summary"],
    queryFn: async () => (await analyticsApi.summary()).data,
  });

  const { data: trends } = useQuery({
    queryKey: ["analytics-trends"],
    queryFn: async () => (await analyticsApi.trends(undefined, undefined, "monthly")).data,
  });

  const { data: categories } = useQuery({
    queryKey: ["analytics-categories"],
    queryFn: async () => (await analyticsApi.categories()).data,
  });

  const { data: focus } = useQuery({
    queryKey: ["analytics-focus", focusNames.join(",")],
    queryFn: async () => (await analyticsApi.focusCategories(focusNames)).data,
  });

  const { data: insights } = useQuery({
    queryKey: ["analytics-insights"],
    queryFn: async () => (await analyticsApi.insights()).data,
  });

  const trendData = useMemo(() => {
    return (
      trends?.data_points?.map((point: any) => ({
        month: format(new Date(point.date), "MMM"),
        income: Number(point.income),
        expenses: Number(point.expenses),
        savings: Number(point.net),
      })) || []
    );
  }, [trends]);

  const categoryData = useMemo(() => {
    return (
      categories?.categories?.map((category: any, index: number) => ({
        name: category.category_name,
        value: Number(category.amount),
        color: category.category_color || generateColor(index),
      })) || []
    );
  }, [categories]);

  type FocusCategorySummary = {
    name: string;
    amount: number;
    count: number;
  };

  const focusData = useMemo<FocusCategorySummary[]>(() => {
    return (
      focus?.categories?.map((item: any) => ({
        name: item.category_name,
        amount: Number(item.amount ?? 0),
        count: Number(item.transaction_count ?? 0),
      })) || []
    );
  }, [focus]);

  const topCategory = categoryData[0];
  const totalIncome = Number(summary?.total_income ?? 0);
  const totalExpenses = Number(summary?.total_expenses ?? 0);
  const savings = Number(summary?.net_savings ?? 0);
  const savingsRate = Number(summary?.savings_rate ?? 0);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        <SummaryCard
          title="Total Income"
          value={totalIncome}
          icon={<TrendingUp className="h-4 w-4 text-income" />}
        />
        <SummaryCard
          title="Total Expenses"
          value={totalExpenses}
          icon={<TrendingDown className="h-4 w-4 text-expense" />}
        />
        <SummaryCard
          title="Net Savings"
          value={savings}
          icon={<IndianRupee className="h-4 w-4 text-primary" />}
          subtitle={`${savingsRate.toFixed(1)}% savings rate`}
        />
        <SummaryCard
          title="Top Expense"
          value={topCategory?.value ?? 0}
          icon={<AlertCircle className="h-4 w-4 text-warning" />}
          subtitle={topCategory?.name ?? "No data yet"}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border bg-card p-6">
          <h3 className="mb-4 font-semibold">Income vs Expenses Trend</h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="month" className="text-xs" />
              <YAxis className="text-xs" tickFormatter={(v) => `₹${v / 1000}k`} />
              <Tooltip
                formatter={(value: number) => [formatCurrency(value), ""]}
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                }}
              />
              <Legend />
              <Line type="monotone" dataKey="income" stroke="#22c55e" strokeWidth={2} name="Income" />
              <Line type="monotone" dataKey="expenses" stroke="#ef4444" strokeWidth={2} name="Expenses" />
              <Line type="monotone" dataKey="savings" stroke="#3b82f6" strokeWidth={2} name="Savings" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-lg border bg-card p-6">
          <h3 className="mb-4 font-semibold">Spending by Category</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={categoryData}
                dataKey="value"
                nameKey="name"
                innerRadius={60}
                outerRadius={100}
              >
                {categoryData.map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => [formatCurrency(value), ""]} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border bg-card p-6">
          <h3 className="mb-4 font-semibold">Focus Categories</h3>
          <div className="space-y-4">
            {focusData.map((item) => (
              <div key={item.name} className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{item.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {item.count} transactions
                  </p>
                </div>
                <span className="font-semibold">{formatCurrency(item.amount)}</span>
              </div>
            ))}
            {focusData.length === 0 && (
              <p className="text-sm text-muted-foreground">
                Upload statements to see petrol, food, utilities, clothes, and groceries totals.
              </p>
            )}
          </div>
        </div>

        <div className="rounded-lg border bg-card p-6">
          <h3 className="mb-4 font-semibold">Category Comparison</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={categoryData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="name" className="text-xs" />
              <YAxis className="text-xs" tickFormatter={(v) => `₹${v / 1000}k`} />
              <Tooltip formatter={(value: number) => [formatCurrency(value), ""]} />
              <Bar dataKey="value" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-lg border bg-card p-6">
        <h3 className="mb-4 font-semibold">AI Insights</h3>
        <div className="space-y-3">
          {(insights?.insights || []).map((insight: any) => (
            <div
              key={insight.id}
              className="flex items-start gap-3 rounded-md border p-3"
            >
              <Lightbulb className="mt-0.5 h-4 w-4 text-primary" />
              <div>
                <p className="font-medium">{insight.title}</p>
                <p className="text-sm text-muted-foreground">
                  {insight.message || insight.description}
                </p>
                {insight.action || insight.action_suggestion ? (
                  <p className="mt-1 text-xs text-muted-foreground">
                    {insight.action || insight.action_suggestion}
                  </p>
                ) : null}
              </div>
            </div>
          ))}
          {(insights?.insights || []).length === 0 && (
            <p className="text-sm text-muted-foreground">
              Insights will appear once transactions are analyzed.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function SummaryCard({
  title,
  value,
  icon,
  subtitle,
}: {
  title: string;
  value: number;
  icon: ReactNode;
  subtitle?: string;
}) {
  return (
    <div className="rounded-lg border bg-card p-6">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">{title}</span>
        {icon}
      </div>
      <div className="mt-2 text-2xl font-bold">{formatCurrency(value)}</div>
      {subtitle && <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>}
    </div>
  );
}
