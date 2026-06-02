import React, { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface KpiCardProps {
  spec: {
    props: {
      title?: string;
      value?: string | number;
      prefix?: string;
      suffix?: string;
      trend?: "up" | "down" | "flat";
      trendValue?: string;
      color?: string;
    };
  };
  dataSourceRef?: string;
}

export function KpiCard({ spec, dataSourceRef }: KpiCardProps) {
  const [value, setValue] = useState(spec.props.value);
  const { title, prefix, suffix, trend, trendValue, color } = spec.props;

  useEffect(() => {
    if (!dataSourceRef) return;
    const requestId = `kpi-${Date.now()}`;
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail.requestId === requestId && detail.data?.rows?.[0]) {
        const row = detail.data.rows[0];
        setValue(Object.values(row)[0] as string);
      }
    };
    window.addEventListener("sandbox-data", handler);
    window.parent.postMessage({ type: "data-request", requestId, dataSourceRef, aggregate: true }, "*");
    return () => window.removeEventListener("sandbox-data", handler);
  }, [dataSourceRef]);

  const TrendIcon = trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;
  const trendColor = trend === "up" ? "text-green-500" : trend === "down" ? "text-red-500" : "text-gray-400";

  return (
    <div className="border rounded-lg bg-white p-6">
      <p className="text-sm text-gray-500 mb-1">{title || "Metric"}</p>
      <p className="text-3xl font-bold" style={{ color: color || "#111" }}>
        {prefix}{value ?? "—"}{suffix}
      </p>
      {trend && (
        <div className={`flex items-center gap-1 mt-2 ${trendColor} text-sm`}>
          <TrendIcon className="h-4 w-4" />
          {trendValue && <span>{trendValue}</span>}
        </div>
      )}
    </div>
  );
}
