import { Suspense } from "react";
import { DashboardStats } from "@/components/dashboard/DashboardStats";
import { SpendingChart } from "@/components/charts/SpendingChart";
import { RecentTransactions } from "@/components/dashboard/RecentTransactions";
import { CategoryPieChart } from "@/components/charts/CategoryPieChart";
import { InsightsCard } from "@/components/dashboard/InsightsCard";

export const metadata = {
  title: "Dashboard",
};

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Overview of your financial health
        </p>
      </div>

      {/* Stats Cards */}
      <Suspense fallback={<div>Loading stats...</div>}>
        <DashboardStats />
      </Suspense>

      {/* Charts Row */}
      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border bg-card p-6">
          <h2 className="mb-4 font-semibold">Spending Trends</h2>
          <Suspense fallback={<div>Loading chart...</div>}>
            <SpendingChart />
          </Suspense>
        </div>
        <div className="rounded-lg border bg-card p-6">
          <h2 className="mb-4 font-semibold">Spending by Category</h2>
          <Suspense fallback={<div>Loading chart...</div>}>
            <CategoryPieChart />
          </Suspense>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid gap-6 md:grid-cols-3">
        <div className="md:col-span-2 rounded-lg border bg-card p-6">
          <h2 className="mb-4 font-semibold">Recent Transactions</h2>
          <Suspense fallback={<div>Loading transactions...</div>}>
            <RecentTransactions />
          </Suspense>
        </div>
        <div className="rounded-lg border bg-card p-6">
          <h2 className="mb-4 font-semibold">AI Insights</h2>
          <Suspense fallback={<div>Loading insights...</div>}>
            <InsightsCard />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
