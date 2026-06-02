import React, { useEffect, useState } from "react";
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface LineChartProps {
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

export function LineChart({ spec, dataSourceRef }: LineChartProps) {
  const [data, setData] = useState<any[]>([]);
  const { title, xKey = "name", yKey = "value", color = "#3b82f6" } = spec.props;

  useEffect(() => {
    if (!dataSourceRef) return;
    const requestId = `line-${Date.now()}`;
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
      <h3 className="font-semibold text-gray-900 mb-4">{title || "Line Chart"}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <RechartsLineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xKey} />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey={yKey} stroke={color} strokeWidth={2} dot={{ r: 4 }} />
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  );
}
