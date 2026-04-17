"use client";

import { useQuery } from "@tanstack/react-query";
import { Lightbulb, AlertTriangle, TrendingUp } from "lucide-react";
import { analyticsApi } from "@/lib/api";

const severityStyles: Record<string, string> = {
  warning: "border-amber-200 bg-amber-50",
  alert: "border-red-200 bg-red-50",
  info: "border-blue-200 bg-blue-50",
  tip: "border-blue-200 bg-blue-50",
};

export function InsightsCard() {
  const { data } = useQuery({
    queryKey: ["dashboard-insights"],
    queryFn: async () => (await analyticsApi.insights()).data,
  });

  const insights = data?.insights || [];

  return (
    <div className="space-y-4">
      {insights.map((insight: any) => {
        const severity = insight.severity || insight.type || "info";
        const Icon =
          severity === "warning" || severity === "alert"
            ? AlertTriangle
            : severity === "success"
            ? TrendingUp
            : Lightbulb;

        return (
          <div
            key={insight.id}
            className={`rounded-md border p-3 ${severityStyles[severity] || severityStyles.info}`}
          >
            <div className="flex items-start gap-3">
              <Icon className="h-5 w-5 text-blue-600" />
              <div>
                <p className="font-medium">{insight.title}</p>
                <p className="text-sm text-muted-foreground">
                  {insight.message || insight.description}
                </p>
              </div>
            </div>
          </div>
        );
      })}
      {insights.length === 0 && (
        <p className="text-sm text-muted-foreground">
          Insights will appear after your first upload.
        </p>
      )}
    </div>
  );
}
