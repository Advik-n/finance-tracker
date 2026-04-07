"use client";

import { formatCurrency, formatDate } from "@/lib/utils";

// Mock data - replace with API call
const transactions = [
  {
    id: "1",
    description: "Grocery Store",
    merchant: "Whole Foods",
    amount: -125.5,
    date: "2024-01-15",
    category: { name: "Groceries", color: "#10b981" },
  },
  {
    id: "2",
    description: "Salary Deposit",
    merchant: "Employer Inc",
    amount: 5000,
    date: "2024-01-14",
    category: { name: "Income", color: "#3b82f6" },
  },
  {
    id: "3",
    description: "Electric Bill",
    merchant: "Power Company",
    amount: -145.0,
    date: "2024-01-13",
    category: { name: "Utilities", color: "#f59e0b" },
  },
  {
    id: "4",
    description: "Restaurant",
    merchant: "Italian Bistro",
    amount: -78.5,
    date: "2024-01-12",
    category: { name: "Dining", color: "#ef4444" },
  },
  {
    id: "5",
    description: "Gas Station",
    merchant: "Shell",
    amount: -52.0,
    date: "2024-01-11",
    category: { name: "Transportation", color: "#8b5cf6" },
  },
];

export function RecentTransactions() {
  return (
    <div className="space-y-4">
      {transactions.map((transaction) => (
        <div
          key={transaction.id}
          className="flex items-center justify-between py-2"
        >
          <div className="flex items-center gap-3">
            <div
              className="h-10 w-10 rounded-full"
              style={{ backgroundColor: transaction.category.color + "20" }}
            >
              <div
                className="flex h-full w-full items-center justify-center rounded-full text-xs font-bold"
                style={{ color: transaction.category.color }}
              >
                {transaction.category.name[0]}
              </div>
            </div>
            <div>
              <p className="font-medium">{transaction.description}</p>
              <p className="text-sm text-muted-foreground">
                {transaction.merchant} • {formatDate(transaction.date)}
              </p>
            </div>
          </div>
          <span
            className={`font-semibold ${
              transaction.amount > 0 ? "text-income" : "text-foreground"
            }`}
          >
            {transaction.amount > 0 ? "+" : ""}
            {formatCurrency(transaction.amount)}
          </span>
        </div>
      ))}
    </div>
  );
}
