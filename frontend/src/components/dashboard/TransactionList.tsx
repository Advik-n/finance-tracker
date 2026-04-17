"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { formatCurrency, formatDate, generateColor } from "@/lib/utils";
import { Pencil, Trash2 } from "lucide-react";
import { transactionsApi } from "@/lib/api";

export function TransactionList() {
  const { data } = useQuery({
    queryKey: ["transactions", 1],
    queryFn: async () =>
      (
        await transactionsApi.list({
          page: 1,
          page_size: 20,
        })
      ).data,
  });

  const transactions = useMemo(() => data?.items || [], [data]);

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
          {transactions.map((transaction: any, index: number) => {
            const amount =
              transaction.transaction_type === "CREDIT"
                ? Number(transaction.amount)
                : -Number(transaction.amount);
            const color = transaction.category?.color || generateColor(index);

            return (
            <tr key={transaction.id} className="hover:bg-muted/30">
              <td className="px-4 py-3 text-sm">
                {formatDate(transaction.transaction_date)}
              </td>
              <td className="px-4 py-3">
                <div>
                  <p className="font-medium">
                    {transaction.description || transaction.merchant_name}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {transaction.merchant_name || "Unknown"}
                  </p>
                </div>
              </td>
              <td className="px-4 py-3">
                <span
                  className="inline-flex rounded-full px-2 py-1 text-xs font-medium"
                  style={{
                    backgroundColor: color + "20",
                    color,
                  }}
                >
                  {transaction.category?.name || "Uncategorized"}
                </span>
              </td>
              <td
                className={`px-4 py-3 text-right font-semibold ${
                  amount > 0 ? "text-income" : ""
                }`}
              >
                {amount > 0 ? "+" : ""}
                {formatCurrency(Math.abs(amount))}
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
          );
          })}
          {transactions.length === 0 && (
            <tr>
              <td className="px-4 py-6 text-center text-sm text-muted-foreground" colSpan={5}>
                No transactions yet. Upload a statement to populate this list.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
