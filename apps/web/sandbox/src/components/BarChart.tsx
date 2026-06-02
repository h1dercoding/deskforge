import React, { useEffect, useState } from "react";
import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface BarChartProps {
  spec: {
    props: {
      title?: string;
      xKey?: string;
      yKey?: string;
      color?: string;
    };
  };
  dataSourceRef?: string;
}

export function BarChart({ spec, dataSourceRef }: BarChartProps) {
  const [data, setData] = useState<any[]>([]);
  const { title, xKey = "name", yKey = "value", color = "#3b82f6" } = spec.props;

  useEffect(() => {
    if (!dataSourceRef) return;
    const requestId = `bar-${Date.now()}`;
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail.requestId === requestId) setData(detail.data?.rows || []);
    };
    window.addEventListener("sandbox-data", handler);
    window.parent.postMessage({ type: "data-request", requestId, dataSourceRef }, "*");
    return () => window.removeEventListener("sandbox-data", handler);
  }, [dataSourceRef]);

  return (
    <div className="border rounded-lg bg-white p-6">
      <h3 className="font-semibold text-gray-900 mb-4">{title || "Bar Chart"}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <RechartsBarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xKey} />
          <YAxis />
          <Tooltip />
          <Bar dataKey={yKey} fill={color} radius={[4, 4, 0, 0]} />
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  );
}
