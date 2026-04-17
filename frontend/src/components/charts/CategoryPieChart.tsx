"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import { analyticsApi } from "@/lib/api";
import { formatCurrency, generateColor } from "@/lib/utils";

export function CategoryPieChart() {
  const { data } = useQuery({
    queryKey: ["category-breakdown"],
    queryFn: async () => (await analyticsApi.categories()).data,
  });

  const chartData = useMemo(() => {
    return (
      data?.categories?.map((category: any, index: number) => ({
        name: category.category_name,
        value: Number(category.amount),
        color: category.category_color || generateColor(index),
      })) || []
    );
  }, [data]);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={2}
          dataKey="value"
        >
          {chartData.map((entry: any, index: number) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "8px",
          }}
          formatter={(value: number) => [formatCurrency(value), ""]}
        />
        <Legend
          verticalAlign="bottom"
          height={36}
          formatter={(value) => (
            <span className="text-sm text-foreground">{value}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
