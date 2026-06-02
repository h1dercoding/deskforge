/**
 * DeskForge — API Request/Response Types
 *
 * TypeScript types matching the FastAPI OpenAPI 3.1 contract.
 * Both frontend and backend should reference these types.
 */

import type { ToolSpec, ToolTheme } from "./tool-spec";

// ── Common ──────────────────────────────────────────────────

export interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
}

export interface ApiResponse<T> {
  data: T;
  meta?: PaginationMeta;
}

export interface ApiError {
  error: {
    code: number;
    type: string;
    message: string;
    details?: Array<{ field: string; issue: string; value?: unknown }>;
    request_id: string;
    timestamp: string;
  };
}

// ── Auth ────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  email_verified: boolean;
  auth_provider: "local" | "google";
  created_at: string;
  updated_at: string;
}

export interface Tokens {
  access_token: string;
  refresh_token: string;
  token_type: "Bearer";
  expires_in: number; // seconds
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface GoogleLoginRequest {
  id_token: string;
}

export interface VerifyEmailRequest {
  token: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface UpdateProfileRequest {
  name?: string;
  email?: string;
  avatar_url?: string;
}

// ── Teams ───────────────────────────────────────────────────

export type TeamPlan = "free" | "starter" | "pro" | "enterprise";
export type TeamRole = "owner" | "editor" | "viewer";

export interface Team {
  id: string;
  name: string;
  owner_id: string;
  plan: TeamPlan;
  trial_ends_at?: string;
  created_at: string;
  updated_at: string;
}

export interface TeamMember {
  id: string;
  team_id: string;
  user_id: string;
  user: User;
  role: TeamRole;
  invited_at: string;
  accepted_at?: string;
}

export interface TeamInvitation {
  id: string;
  team_id: string;
  email: string;
  role: TeamRole;
  token: string;
  expires_at: string;
  accepted_at?: string;
  created_at: string;
}

export interface InviteMemberRequest {
  email: string;
  role: TeamRole;
}

export interface UpdateMemberRequest {
  role: TeamRole;
}

export interface UpdateTeamRequest {
  name: string;
}

// ── Tools ───────────────────────────────────────────────────

export type ToolVisibility = "public" | "private";
export type ToolStatus = "draft" | "active" | "archived";

export interface Tool {
  id: string;
  team_id: string;
  created_by: string;
  data_source_id?: string;
  name: string;
  slug: string;
  description?: string;
  prompt: string;
  spec: ToolSpec;
  visibility: ToolVisibility;
  theme: ToolTheme;
  status: ToolStatus;
  created_at: string;
  updated_at: string;
}

export interface ToolVersion {
  id: string;
  tool_id: string;
  version_number: number;
  prompt: string;
  spec: ToolSpec;
  created_by: string;
  created_at: string;
}

export interface CreateToolRequest {
  name: string;
  prompt: string;
  spec: ToolSpec;
  data_source_id?: string;
}

export interface UpdateToolRequest {
  name?: string;
  description?: string;
  theme?: ToolTheme;
}

export interface UpdateSharingRequest {
  visibility: ToolVisibility;
}

// ── Generation ──────────────────────────────────────────────

export interface GenerateRequest {
  prompt: string;
  data_source_id?: string;
  template_id?: string;
}

export interface IterateRequest {
  message: string;
}

export interface ClarifyRequest {
  session_id: string;
  answers: string[];
}

export interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  prompt: string;
  spec: ToolSpec;
  created_at: string;
}

// ── Data Sources ────────────────────────────────────────────

export type DataSourceType = "csv" | "google_sheets" | "postgresql" | "mysql";
export type DataSourceStatus = "connected" | "disconnected" | "error";

export interface DataSource {
  id: string;
  team_id: string;
  name: string;
  type: DataSourceType;
  config: Record<string, unknown>;
  schema?: DataSourceColumn[];
  status: DataSourceStatus;
  row_count: number;
  created_at: string;
  updated_at: string;
}

export interface DataSourceColumn {
  name: string;
  type: string;
  nullable?: boolean;
  sample_values?: unknown[];
}

export interface DatabaseConnectionRequest {
  type: "postgresql" | "mysql";
  host: string;
  port: number;
  database: string;
  user: string;
  password: string;
  ssl?: boolean;
  readonly?: boolean;
}

export interface GoogleSheetsRequest {
  sheet_url: string;
  tab_name?: string;
}

export interface QueryRequest {
  query: {
    filter?: Record<string, unknown>;
    sort?: Array<{ field: string; direction: "asc" | "desc" }>;
    page?: number;
    per_page?: number;
  };
}

export interface QueryResponse {
  rows: Record<string, unknown>[];
  total: number;
}

// ── Billing ─────────────────────────────────────────────────

export interface Subscription {
  plan: TeamPlan;
  usage: {
    tools: { used: number; limit: number };
    members: { used: number; limit: number };
    datasources: { used: number; limit: number };
  };
  trial_ends_at?: string;
  current_period_end?: string;
}

export interface CheckoutRequest {
  plan: TeamPlan;
}

export interface UsageStats {
  tools: { used: number; limit: number };
  members: { used: number; limit: number };
  datasources: { used: number; limit: number };
}

// ── Sharing ─────────────────────────────────────────────────

export interface ShareLink {
  id: string;
  tool_id: string;
  token: string;
  is_active: boolean;
  created_at: string;
}

export interface SharedToolView {
  tool: Tool;
  is_public: boolean;
}

// ── Health ──────────────────────────────────────────────────

export interface HealthResponse {
  status: "ok";
  version: string;
  uptime: number;
}

export interface ReadinessResponse {
  status: "ready" | "not_ready";
  checks: {
    db: "ok" | "error";
    redis: "ok" | "error";
  };
}
