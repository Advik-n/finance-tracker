"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { formatCurrency, formatDate, generateColor } from "@/lib/utils";
import { transactionsApi } from "@/lib/api";

export function RecentTransactions() {
  const { data } = useQuery({
    queryKey: ["recent-transactions"],
    queryFn: async () =>
      (
        await transactionsApi.list({
          page: 1,
          page_size: 5,
        })
      ).data,
  });

  const transactions = useMemo(() => data?.items || [], [data]);

  return (
    <div className="space-y-4">
      {transactions.map((transaction: any, index: number) => {
        const amount =
          transaction.transaction_type === "CREDIT"
            ? Number(transaction.amount)
            : -Number(transaction.amount);
        const color = transaction.category?.color || generateColor(index);

        return (
          <div
            key={transaction.id}
            className="flex items-center justify-between py-2"
          >
            <div className="flex items-center gap-3">
              <div
                className="h-10 w-10 rounded-full"
                style={{ backgroundColor: color + "20" }}
              >
                <div
                  className="flex h-full w-full items-center justify-center rounded-full text-xs font-bold"
                  style={{ color }}
                >
                  {(transaction.category?.name || "?")[0]}
                </div>
              </div>
              <div>
                <p className="font-medium">
                  {transaction.description || transaction.merchant_name}
                </p>
                <p className="text-sm text-muted-foreground">
                  {transaction.merchant_name || "Unknown"} •{" "}
                  {formatDate(transaction.transaction_date)}
                </p>
              </div>
            </div>
            <span
              className={`font-semibold ${
                amount > 0 ? "text-income" : "text-foreground"
              }`}
            >
              {amount > 0 ? "+" : ""}
              {formatCurrency(Math.abs(amount))}
            </span>
          </div>
        );
      })}
      {transactions.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No transactions yet. Upload a statement to get started.
        </p>
      )}
    </div>
  );
}
