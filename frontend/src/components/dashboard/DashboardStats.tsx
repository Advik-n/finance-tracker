"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { TrendingUp, TrendingDown, DollarSign, CreditCard } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import { analyticsApi } from "@/lib/api";

export function DashboardStats() {
  const { data, isLoading } = useQuery({
    queryKey: ["analytics-summary"],
    queryFn: async () => (await analyticsApi.summary()).data,
  });

  const stats = useMemo(() => {
    const incomeChange = data?.income_change ?? 0;
    const expenseChange = data?.expense_change ?? 0;
    const savingsChange = data?.savings_change ?? 0;

    return [
      {
        name: "Total Income",
        value: Number(data?.total_income ?? 0),
        change: incomeChange,
        changeType: incomeChange >= 0 ? "positive" : "negative",
        icon: TrendingUp,
      },
      {
        name: "Total Expenses",
        value: Number(data?.total_expenses ?? 0),
        change: expenseChange,
        changeType: expenseChange >= 0 ? "negative" : "positive",
        icon: TrendingDown,
      },
      {
        name: "Net Savings",
        value: Number(data?.net_savings ?? 0),
        change: savingsChange,
        changeType: savingsChange >= 0 ? "positive" : "negative",
        icon: DollarSign,
      },
      {
        name: "Transactions",
        value: Number(data?.transaction_count ?? 0),
        change: 0,
        changeType: "neutral",
        icon: CreditCard,
      },
    ] as const;
  }, [data]);

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <div key={stat.name} className="rounded-lg border bg-card p-6">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">
              {stat.name}
            </span>
            <stat.icon
              className={`h-5 w-5 ${
                stat.changeType === "positive"
                  ? "text-income"
                  : stat.changeType === "negative"
                  ? "text-expense"
                  : "text-muted-foreground"
              }`}
            />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold">
              {stat.name === "Transactions"
                ? stat.value
                : formatCurrency(stat.value)}
            </span>
          </div>
          <div className="mt-1 flex items-center gap-1">
            {stat.name !== "Transactions" && (
              <>
                <span
                  className={`text-sm ${
                    stat.changeType === "positive"
                      ? "text-income"
                      : stat.changeType === "negative"
                      ? "text-expense"
                      : "text-muted-foreground"
                  }`}
                >
                  {stat.change > 0 ? "+" : ""}
                  {stat.change}%
                </span>
                <span className="text-sm text-muted-foreground">vs last month</span>
              </>
            )}
            {isLoading && (
              <span className="text-sm text-muted-foreground">Loading…</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
