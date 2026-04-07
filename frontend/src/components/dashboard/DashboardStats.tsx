"use client";

import { TrendingUp, TrendingDown, DollarSign, CreditCard } from "lucide-react";
import { formatCurrency } from "@/lib/utils";

// Mock data - replace with API call
const stats = [
  {
    name: "Total Income",
    value: 8450.0,
    change: 12.5,
    changeType: "positive" as const,
    icon: TrendingUp,
  },
  {
    name: "Total Expenses",
    value: 5230.0,
    change: 8.2,
    changeType: "negative" as const,
    icon: TrendingDown,
  },
  {
    name: "Net Savings",
    value: 3220.0,
    change: 23.1,
    changeType: "positive" as const,
    icon: DollarSign,
  },
  {
    name: "Transactions",
    value: 147,
    change: 5.4,
    changeType: "neutral" as const,
    icon: CreditCard,
  },
];

export function DashboardStats() {
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
            <span
              className={`text-sm ${
                stat.changeType === "positive"
                  ? "text-income"
                  : stat.changeType === "negative"
                  ? "text-expense"
                  : "text-muted-foreground"
              }`}
            >
              {stat.changeType === "positive" ? "+" : ""}
              {stat.change}%
            </span>
            <span className="text-sm text-muted-foreground">vs last month</span>
          </div>
        </div>
      ))}
    </div>
  );
}
