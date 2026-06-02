import React from "react";
import { DataTable } from "./components/DataTable";
import { Form } from "./components/Form";
import { KpiCard } from "./components/KpiCard";
import { BarChart } from "./components/BarChart";
import { LineChart } from "./components/LineChart";
import { PieChart } from "./components/PieChart";

interface ComponentSpec {
  id: string;
  type: string;
  position: { row: number; col: number; colSpan?: number; rowSpan?: number };
  props: Record<string, any>;
  dataSourceRef?: string;
}

interface ToolSpec {
  version: number;
  name: string;
  layout: { type: string; columns: number; gap?: string };
  components: ComponentSpec[];
  dataSources?: any[];
  actions?: any[];
}

const COMPONENT_MAP: Record<string, React.ComponentType<any>> = {
  dataTable: DataTable,
  form: Form,
  kpiCard: KpiCard,
  barChart: BarChart,
  lineChart: LineChart,
  pieChart: PieChart,
};

function TextComponent({ props }: { props: Record<string, any> }) {
  return <p className="text-gray-700">{props.content || props.text || ""}</p>;
}

function DividerComponent() {
  return <hr className="border-gray-200 my-4" />;
}

export function SandboxRenderer({ spec }: { spec: ToolSpec }) {
  if (!spec || !spec.components) {
    return <div className="p-8 text-center text-gray-400">No components to render</div>;
  }

  const columns = spec.layout?.columns || 12;
  const gap = spec.layout?.gap || "1rem";

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6 text-gray-900">{spec.name}</h1>
      <div
        className="grid"
        style={{
          gridTemplateColumns: `repeat(${columns}, 1fr)`,
          gap,
        }}
      >
        {spec.components.map((comp) => {
          const Component = COMPONENT_MAP[comp.type];
          const colSpan = comp.position?.colSpan || 12;
          const style: React.CSSProperties = {
            gridColumn: `span ${Math.min(colSpan, columns)}`,
          };

          if (comp.type === "text") {
            return (
              <div key={comp.id} style={style}>
                <TextComponent props={comp.props} />
              </div>
            );
          }
          if (comp.type === "divider") {
            return (
              <div key={comp.id} style={style}>
                <DividerComponent />
              </div>
            );
          }
          if (!Component) {
            return (
              <div key={comp.id} style={style} className="p-4 bg-red-50 rounded text-red-500 text-sm">
                Unknown component: {comp.type}
              </div>
            );
          }
          return (
            <div key={comp.id} style={style}>
              <Component spec={comp} dataSourceRef={comp.dataSourceRef} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
