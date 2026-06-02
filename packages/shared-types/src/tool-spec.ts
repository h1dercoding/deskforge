/**
 * DeskForge — Tool Specification Types
 *
 * This defines the JSON schema that the LLM generates and the sandbox renders.
 * It's the critical contract between the generation pipeline and the renderer.
 *
 * Version: 1
 */

// ── Layout ──────────────────────────────────────────────────

export interface ToolLayout {
  type: "grid" | "single-column";
  columns: number; // 1-12
  gap?: string; // CSS gap value, default "1rem"
}

// ── Data Sources ────────────────────────────────────────────

export type DataSourceType = "csv" | "google_sheets" | "postgresql" | "mysql";

export interface DataSourceQuery {
  select?: string[];
  filter?: Record<string, unknown>;
  sort?: Array<{ field: string; direction: "asc" | "desc" }>;
  aggregate?: Record<string, unknown>;
}

export interface ToolDataSource {
  id: string;
  type: DataSourceType;
  connectionId?: string; // References a data_sources.id
  table?: string;
  query?: DataSourceQuery;
}

// ── Component Types ─────────────────────────────────────────

export type ComponentType =
  | "dataTable"
  | "form"
  | "kpiCard"
  | "barChart"
  | "lineChart"
  | "pieChart"
  | "text"
  | "divider";

export interface ComponentPosition {
  row: number;
  col: number;
  colSpan?: number; // default 12
  rowSpan?: number; // default 1
}

// ── Component Props ─────────────────────────────────────────

export interface DataTableColumn {
  key: string;
  label: string;
  type?: "text" | "number" | "date" | "boolean" | "currency";
  sortable?: boolean;
  width?: string;
}

export interface DataTableProps {
  columns?: DataTableColumn[];
  sortable?: boolean;
  filterable?: boolean;
  paginated?: boolean;
  pageSize?: number; // default 25
  searchable?: boolean;
  exportable?: boolean;
}

export interface FormField {
  name: string;
  type: "text" | "number" | "email" | "password" | "select" | "textarea" | "date" | "checkbox" | "file";
  label: string;
  placeholder?: string;
  required?: boolean;
  options?: Array<{ label: string; value: string }>; // For select fields
  validation?: Record<string, unknown>;
}

export interface FormProps {
  fields?: FormField[];
  submitLabel?: string;
  layout?: "vertical" | "inline" | "horizontal";
  submitAction?: string; // References an actions[].id
}

export interface KpiCardProps {
  title: string;
  format?: "number" | "currency" | "percent" | "text";
  prefix?: string;
  suffix?: string;
  comparison?: {
    enabled: boolean;
    direction: "up" | "down";
    value: number;
    format?: "number" | "percent";
  };
}

export interface ChartProps {
  title?: string;
  xKey?: string;
  yKey?: string;
  nameKey?: string;
  valueKey?: string;
  color?: string;
  colors?: string[];
  showLegend?: boolean;
  showGrid?: boolean;
  height?: number;
}

export interface TextProps {
  content: string;
  variant?: "h1" | "h2" | "h3" | "p" | "blockquote";
  align?: "left" | "center" | "right";
}

export interface DividerProps {
  orientation?: "horizontal" | "vertical";
  label?: string;
}

// ── Component ───────────────────────────────────────────────

export interface ToolComponent {
  id: string;
  type: ComponentType;
  position: ComponentPosition;
  props?: Record<string, unknown>; // Component-specific props
  dataSourceRef?: string; // References a dataSources[].id
}

// ── Actions ─────────────────────────────────────────────────

export type ActionType = "create" | "update" | "delete";

export interface ToolAction {
  id: string;
  type: ActionType;
  dataSourceRef?: string;
  triggerComponentId?: string;
}

// ── Complete Tool Spec ──────────────────────────────────────

export interface ToolSpec {
  version: 1;
  name: string;
  description?: string;
  layout: ToolLayout;
  dataSources: ToolDataSource[];
  components: ToolComponent[];
  actions?: ToolAction[];
}

// ── Theme ───────────────────────────────────────────────────

export interface ToolTheme {
  primaryColor?: string;
  backgroundColor?: string;
  fontFamily?: string;
  borderRadius?: string;
  darkMode?: boolean;
}

// ── SSE Generation Events ───────────────────────────────────

export type GenerationStep =
  | "analyzing"
  | "classifying"
  | "building_prompt"
  | "generating"
  | "validating"
  | "sanitizing"
  | "rendering"
  | "complete";

export interface GenerationProgressEvent {
  step: GenerationStep;
  message: string;
}

export interface GenerationSpecEvent {
  spec: ToolSpec;
  tool_id?: string;
}

export interface GenerationDoneEvent {
  success: boolean;
  error?: string;
}

export interface GenerationClarifyEvent {
  questions: string[];
  session_id: string;
}
