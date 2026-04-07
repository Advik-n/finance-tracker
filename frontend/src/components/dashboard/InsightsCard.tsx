"use client";

import { Lightbulb, AlertTriangle, TrendingUp } from "lucide-react";

// Mock data - replace with API call
const insights = [
  {
    id: "1",
    type: "recommendation",
    severity: "info",
    title: "Savings Opportunity",
    description: "You could save $150/month by reducing dining expenses.",
    icon: Lightbulb,
  },
  {
    id: "2",
    type: "warning",
    severity: "warning",
    title: "Budget Alert",
    description: "You've used 85% of your Entertainment budget.",
    icon: AlertTriangle,
  },
  {
    id: "3",
    type: "positive",
    severity: "info",
    title: "Great Progress!",
    description: "Your savings rate increased by 5% this month.",
    icon: TrendingUp,
  },
];

export function InsightsCard() {
  return (
    <div className="space-y-4">
      {insights.map((insight) => (
        <div
          key={insight.id}
          className={`rounded-md border p-3 ${
            insight.severity === "warning"
              ? "border-amber-200 bg-amber-50"
              : "border-blue-200 bg-blue-50"
          }`}
        >
          <div className="flex items-start gap-3">
            <insight.icon
              className={`h-5 w-5 ${
                insight.severity === "warning"
                  ? "text-amber-600"
                  : "text-blue-600"
              }`}
            />
            <div>
              <p
                className={`font-medium ${
                  insight.severity === "warning"
                    ? "text-amber-900"
                    : "text-blue-900"
                }`}
              >
                {insight.title}
              </p>
              <p
                className={`text-sm ${
                  insight.severity === "warning"
                    ? "text-amber-700"
                    : "text-blue-700"
                }`}
              >
                {insight.description}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
