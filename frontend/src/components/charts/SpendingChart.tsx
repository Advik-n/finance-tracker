"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// Mock data - replace with API call
const data = [
  { month: "Jan", income: 5200, expenses: 3800 },
  { month: "Feb", income: 5400, expenses: 4200 },
  { month: "Mar", income: 5100, expenses: 3600 },
  { month: "Apr", income: 5800, expenses: 4100 },
  { month: "May", income: 5600, expenses: 3900 },
  { month: "Jun", income: 5900, expenses: 4300 },
];

export function SpendingChart() {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis
          dataKey="month"
          stroke="hsl(var(--muted-foreground))"
          fontSize={12}
        />
        <YAxis
          stroke="hsl(var(--muted-foreground))"
          fontSize={12}
          tickFormatter={(value) => `$${value}`}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "8px",
          }}
          formatter={(value: number) => [`$${value}`, ""]}
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
