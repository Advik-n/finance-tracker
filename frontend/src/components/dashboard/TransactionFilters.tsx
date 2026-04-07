"use client";

export function TransactionFilters() {
  return (
    <div className="flex flex-wrap items-center gap-4">
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium">Date:</label>
        <input
          type="date"
          className="rounded-md border bg-background px-3 py-1.5 text-sm"
        />
        <span className="text-muted-foreground">to</span>
        <input
          type="date"
          className="rounded-md border bg-background px-3 py-1.5 text-sm"
        />
      </div>

      <div className="flex items-center gap-2">
        <label className="text-sm font-medium">Category:</label>
        <select className="rounded-md border bg-background px-3 py-1.5 text-sm">
          <option value="">All Categories</option>
          <option value="groceries">Groceries</option>
          <option value="dining">Dining</option>
          <option value="utilities">Utilities</option>
          <option value="transportation">Transportation</option>
          <option value="entertainment">Entertainment</option>
        </select>
      </div>

      <div className="flex items-center gap-2">
        <label className="text-sm font-medium">Type:</label>
        <select className="rounded-md border bg-background px-3 py-1.5 text-sm">
          <option value="">All Types</option>
          <option value="expense">Expense</option>
          <option value="income">Income</option>
        </select>
      </div>

      <button className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground">
        Apply Filters
      </button>
    </div>
  );
}
