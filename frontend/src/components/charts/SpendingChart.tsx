"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { subMonths, format } from "date-fns";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { analyticsApi } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

export function SpendingChart() {
  const endDate = new Date();
  const startDate = subMonths(endDate, 5);
  const startDateStr = startDate.toISOString().split("T")[0];
  const endDateStr = endDate.toISOString().split("T")[0];

  const { data } = useQuery({
    queryKey: ["spending-trends", startDateStr, endDateStr],
    queryFn: async () =>
      (await analyticsApi.trends(startDateStr, endDateStr, "monthly")).data,
  });

  const chartData = useMemo(() => {
    return (
      data?.data_points?.map((point: any) => ({
        month: format(new Date(point.date), "MMM"),
        income: Number(point.income),
        expenses: Number(point.expenses),
      })) || []
    );
  }, [data]);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis
          dataKey="month"
          stroke="hsl(var(--muted-foreground))"
          fontSize={12}
        />
        <YAxis
          stroke="hsl(var(--muted-foreground))"
          fontSize={12}
          tickFormatter={(value) => formatCurrency(value as number)}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "8px",
          }}
          formatter={(value: number) => [formatCurrency(value), ""]}
        />
        <Line
          type="monotone"
          dataKey="income"
          stroke="hsl(142, 76%, 36%)"
          strokeWidth={2}
          dot={{ fill: "hsl(142, 76%, 36%)" }}
          name="Income"
        />
        <Line
          type="monotone"
          dataKey="expenses"
          stroke="hsl(0, 84%, 60%)"
          strokeWidth={2}
          dot={{ fill: "hsl(0, 84%, 60%)" }}
          name="Expenses"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
