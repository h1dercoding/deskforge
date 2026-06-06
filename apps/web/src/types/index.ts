// ============================================================
// DeskForge TypeScript Types
// Mirrors the backend API schema
// ============================================================

// Enums
export type AuthProvider = 'local' | 'google';
export type TeamPlan = 'free' | 'starter' | 'pro' | 'enterprise';
export type TeamRole = 'owner' | 'editor' | 'submitter' | 'viewer';
export type ToolVisibility = 'public' | 'private';
export type ToolStatus = 'draft' | 'active' | 'archived';
export type DataSourceType = 'csv' | 'google_sheets' | 'postgresql' | 'mysql';
export type DataSourceStatus = 'connected' | 'disconnected' | 'error';

// User
export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  email_verified: boolean;
  auth_provider: AuthProvider;
  google_id: string | null;
  created_at: string;
  updated_at: string;
}

// Team
export interface Team {
  id: string;
  name: string;
  owner_id: string;
  plan: TeamPlan;
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
  trial_ends_at: string | null;
  created_at: string;
  updated_at: string;
}

// Team Member
export interface TeamMember {
  id: string;
  team_id: string;
  user_id: string;
  role: TeamRole;
  invited_at: string;
  accepted_at: string | null;
  user?: User;
}

// Team Invitation
export interface TeamInvitation {
  id: string;
  team_id: string;
  email: string;
  role: TeamRole;
  token: string;
  expires_at: string;
  accepted_at: string | null;
  created_at: string;
}

// Tool Spec (the core JSON schema)
export interface ToolSpecDataSource {
  id: string;
  type: DataSourceType;
  connectionId?: string;
  table?: string;
  query?: {
    select?: string[];
    filter?: Record<string, unknown>;
    sort?: Array<{ field: string; direction: 'asc' | 'desc' }>;
    aggregate?: Record<string, unknown>;
  };
}

export interface ToolSpecComponent {
  id: string;
  type: 'dataTable' | 'form' | 'kpiCard' | 'barChart' | 'lineChart' | 'pieChart' | 'text' | 'divider';
  position: {
    row: number;
    col: number;
    colSpan?: number;
    rowSpan?: number;
  };
  props?: Record<string, unknown>;
  dataSourceRef?: string;
}

export interface ToolSpecAction {
  id: string;
  type: 'create' | 'update' | 'delete';
  dataSourceRef: string;
  triggerComponentId: string;
}

export interface ToolSpec {
  version: 1;
  name: string;
  description?: string;
  layout: {
    type: 'grid' | 'single-column';
    columns: number;
    gap?: string;
  };
  dataSources: ToolSpecDataSource[];
  components: ToolSpecComponent[];
  actions?: ToolSpecAction[];
}

// Tool
export interface Tool {
  id: string;
  team_id: string;
  created_by: string;
  data_source_id: string | null;
  name: string;
  slug: string;
  description: string | null;
  prompt: string;
  spec: ToolSpec;
  visibility: ToolVisibility;
  theme: ToolTheme;
  status: ToolStatus;
  category: string | null;
  tags: string[] | null;
  created_at: string;
  updated_at: string;
}

// Tool Version
export interface ToolVersion {
  id: string;
  tool_id: string;
  version_number: number;
  prompt: string;
  spec: ToolSpec;
  created_by: string;
  created_at: string;
}

// Tool Theme
export interface ToolTheme {
  primaryColor?: string;
  backgroundColor?: string;
  fontFamily?: string;
  borderRadius?: string;
}

// Data Source
export interface DataSource {
  id: string;
  team_id: string;
  name: string;
  type: DataSourceType;
  config: Record<string, unknown>;
  schema: DataSourceColumn[] | null;
  status: DataSourceStatus;
  row_count: number;
  created_at: string;
  updated_at: string;
}

export interface DataSourceColumn {
  name: string;
  type: string;
  nullable?: boolean;
}

// Share Link
export interface ShareLink {
  id: string;
  tool_id: string;
  token: string;
  is_active: boolean;
  created_at: string;
}

// Plan limits — aligned with backend plan_enforcer.py (source of truth)
// -1 means unlimited
export interface PlanLimits {
  tools: number;    // -1 means unlimited
  members: number;  // -1 means unlimited
  datasources: number; // -1 means unlimited
  generations_per_month: number; // -1 means unlimited (not enforced server-side)
}

export const PLAN_LIMITS: Record<TeamPlan, PlanLimits> = {
  free: { tools: 3, members: 10, datasources: 2, generations_per_month: 50 },
  starter: { tools: -1, members: -1, datasources: 5, generations_per_month: -1 },
  pro: { tools: -1, members: -1, datasources: -1, generations_per_month: -1 },
  enterprise: { tools: -1, members: -1, datasources: -1, generations_per_month: -1 },
};

// Template
export interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  prompt: string;
  spec: ToolSpec;
  thumbnail_url?: string;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  meta?: PaginationMeta;
}

export interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
}

export interface ApiError {
  error: {
    code: number;
    type: string;
    message: string;
    details: Array<{
      field?: string;
      issue: string;
      value?: unknown;
    }>;
    request_id: string;
    timestamp: string;
  };
}

// Auth tokens
export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// SSE Events
export interface SSEProgressEvent {
  step: string;
  message: string;
}

export interface SSESpecEvent {
  spec: ToolSpec;
  tool_id?: string;
}

export interface SSEDoneEvent {
  success: boolean;
}

export interface SSEErrorEvent {
  error: {
    code: number;
    type: string;
    message: string;
  };
}

// Billing
export interface Subscription {
  plan: TeamPlan;
  usage: {
    tools: { used: number; limit: number };
    members: { used: number; limit: number };
    datasources: { used: number; limit: number };
  };
}

// Chat message for iteration
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

// Audit Log
export interface AuditLogEntry {
  id: string;
  timestamp: string;
  user_id: string;
  user_name: string | null;
  user_email: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
}

// Form Submission
export interface FormSubmission {
  id: string;
  data: Record<string, unknown>;
  submitted_by: string | null;
  ip_address: string | null;
  created_at: string;
}
