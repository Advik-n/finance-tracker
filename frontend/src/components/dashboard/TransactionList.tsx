"use client";

import { formatCurrency, formatDate } from "@/lib/utils";
import { MoreHorizontal, Pencil, Trash2 } from "lucide-react";

// Mock data - replace with API call
const transactions = [
  {
    id: "1",
    description: "Grocery Store",
    merchant: "Whole Foods",
    amount: -125.5,
    date: "2024-01-15",
    category: { name: "Groceries", color: "#10b981" },
    type: "expense",
  },
  {
    id: "2",
    description: "Salary Deposit",
    merchant: "Employer Inc",
    amount: 5000,
    date: "2024-01-14",
    category: { name: "Income", color: "#3b82f6" },
    type: "income",
  },
  // Add more transactions...
];

export function TransactionList() {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="border-b bg-muted/50">
          <tr>
            <th className="px-4 py-3 text-left text-sm font-medium">Date</th>
            <th className="px-4 py-3 text-left text-sm font-medium">Description</th>
            <th className="px-4 py-3 text-left text-sm font-medium">Category</th>
            <th className="px-4 py-3 text-right text-sm font-medium">Amount</th>
            <th className="px-4 py-3 text-right text-sm font-medium">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {transactions.map((transaction) => (
            <tr key={transaction.id} className="hover:bg-muted/30">
              <td className="px-4 py-3 text-sm">
                {formatDate(transaction.date)}
              </td>
              <td className="px-4 py-3">
                <div>
                  <p className="font-medium">{transaction.description}</p>
                  <p className="text-sm text-muted-foreground">
                    {transaction.merchant}
                  </p>
                </div>
              </td>
              <td className="px-4 py-3">
                <span
                  className="inline-flex rounded-full px-2 py-1 text-xs font-medium"
                  style={{
                    backgroundColor: transaction.category.color + "20",
                    color: transaction.category.color,
                  }}
                >
                  {transaction.category.name}
                </span>
              </td>
              <td
                className={`px-4 py-3 text-right font-semibold ${
                  transaction.amount > 0 ? "text-income" : ""
                }`}
              >
                {transaction.amount > 0 ? "+" : ""}
                {formatCurrency(transaction.amount)}
              </td>
              <td className="px-4 py-3 text-right">
                <div className="flex items-center justify-end gap-2">
                  <button className="rounded p-1 hover:bg-muted">
                    <Pencil className="h-4 w-4 text-muted-foreground" />
                  </button>
                  <button className="rounded p-1 hover:bg-muted">
                    <Trash2 className="h-4 w-4 text-muted-foreground" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
