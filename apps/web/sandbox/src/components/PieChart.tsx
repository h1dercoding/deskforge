import React, { useEffect, useState } from "react";
import { PieChart as RechartsPieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"];

interface PieChartProps {
  spec: {
    props: {
      title?: string;
      nameKey?: string;
      valueKey?: string;
      variant?: "pie" | "donut";
      colors?: string[];
    };
  };
  dataSourceRef?: string;
}

export function PieChart({ spec, dataSourceRef }: PieChartProps) {
  const [data, setData] = useState<any[]>([]);
  const { title, nameKey = "name", valueKey = "value", variant = "donut", colors = COLORS } = spec.props;

  useEffect(() => {
    if (!dataSourceRef) return;
    const requestId = `pie-${Date.now()}`;
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail.requestId === requestId) setData(detail.data?.rows || []);
    };
    window.addEventListener("sandbox-data", handler);
    window.parent.postMessage({ type: "data-request", requestId, dataSourceRef }, "*");
    return () => window.removeEventListener("sandbox-data", handler);
  }, [dataSourceRef]);

  const innerRadius = variant === "donut" ? 60 : 0;

  return (
    <div className="border rounded-lg bg-white p-6">
      <h3 className="font-semibold text-gray-900 mb-4">{title || "Pie Chart"}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <RechartsPieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius={100}
            paddingAngle={2}
            dataKey={valueKey}
            nameKey={nameKey}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={colors[i % colors.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </RechartsPieChart>
      </ResponsiveContainer>
    </div>
  );
}
