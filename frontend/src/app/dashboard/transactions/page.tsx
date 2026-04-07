import { Suspense } from "react";
import { TransactionList } from "@/components/dashboard/TransactionList";
import { TransactionFilters } from "@/components/dashboard/TransactionFilters";

export const metadata = {
  title: "Transactions",
};

export default function TransactionsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Transactions</h1>
          <p className="text-muted-foreground">
            View and manage all your transactions
          </p>
        </div>
        <button className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90">
          Add Transaction
        </button>
      </div>

      <div className="rounded-lg border bg-card">
        <div className="border-b p-4">
          <TransactionFilters />
        </div>
        <Suspense fallback={<div className="p-4">Loading transactions...</div>}>
          <TransactionList />
        </Suspense>
      </div>
    </div>
  );
}
