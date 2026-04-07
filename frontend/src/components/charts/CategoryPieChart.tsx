"use client";

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import { formatCurrency } from "@/lib/utils";

// Mock data - replace with API call
const data = [
  { name: "Groceries", value: 850, color: "#10b981" },
  { name: "Dining", value: 420, color: "#ef4444" },
  { name: "Utilities", value: 380, color: "#f59e0b" },
  { name: "Transportation", value: 320, color: "#8b5cf6" },
  { name: "Entertainment", value: 280, color: "#3b82f6" },
  { name: "Shopping", value: 450, color: "#ec4899" },
];

export function CategoryPieChart() {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={2}
          dataKey="value"
        >
          {data.map((entry, index) => (
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
