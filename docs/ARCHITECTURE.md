# DeskForge Architecture

**Version:** 1.0.0
**Last Updated:** 2026-06-02

---

## Overview

DeskForge is an AI-powered platform that generates internal tools (dashboards, admin panels, CRUD apps) from natural language descriptions. The architecture follows a **modular monolith** pattern with a FastAPI backend and a Next.js frontend, communicating via a REST API with JWT authentication.

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx (SSL/TLS)                       │
│                    Reverse Proxy + Rate Limiting              │
├──────────────────────┬──────────────────────────────────────┤
│                      │                                       │
│    ┌─────────┐       │       ┌──────────────┐               │
│    │ Next.js │       │       │   FastAPI     │               │
│    │  (Web)  │◄──────┼──────►│   (API)       │               │
│    │ :3000   │  REST  │       │   :8000       │               │
│    └─────────┘       │       └──────┬───────┘               │
│                      │              │                        │
│    ┌─────────┐       │       ┌──────┴───────┐               │
│    │ Sandbox │       │       │              │               │
│    │ (iframe)│       │  ┌────┴────┐  ┌─────┴─────┐         │
│    └─────────┘       │  │Postgres │  │  Redis    │         │
│                      │  │  :5432  │  │  :6379    │         │
│                      │  └─────────┘  └───────────┘         │
│                      │                                       │
│                      │  ┌─────────┐  ┌───────────┐         │
│                      │  │ Stripe  │  │  OpenAI   │         │
│                      │  │   API   │  │   API     │         │
│                      │  └─────────┘  └───────────┘         │
└──────────────────────┴──────────────────────────────────────┘
```

---

## System Components

### Frontend (Next.js 14)

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Web App** | Next.js 14, App Router, React 18 | Main application UI |
| **Sandbox** | Vite, React 18, Tailwind CSS | Isolated tool renderer (iframe) |
| **Shared Types** | TypeScript | Type definitions shared between web and sandbox |
| **State** | Zustand | Client-side state management |
| **UI Library** | shadcn/ui, Tailwind CSS | Component library |

### Backend (FastAPI)

| Module | Purpose | Key Files |
|--------|---------|-----------|
| **auth/** | Registration, login, JWT, OAuth, password reset | `router.py`, `service.py`, `jwt.py`, `password.py` |
| **teams/** | Team CRUD, membership, invitations, RBAC | `router.py`, `service.py`, `permissions.py` |
| **tools/** | Tool CRUD, versioning, slug generation | `router.py`, `service.py`, `versioning.py` |
| **generate/** | LLM generation pipeline, templates, sanitization | `router.py`, `pipeline.py`, `generator.py`, `sanitizer.py` |
| **datasources/** | CSV, Google Sheets, database connectors, query engine | `router.py`, `service.py`, `query_engine.py`, `encryption.py` |
| **billing/** | Stripe checkout, webhooks, plan enforcement | `router.py`, `stripe_service.py`, `webhook_handler.py`, `plan_enforcer.py` |
| **sharing/** | Public/private sharing, share links | `router.py`, `service.py` |
| **models/** | SQLAlchemy ORM models | `user.py`, `team.py`, `tool.py`, `data_source.py`, etc. |
| **middleware/** | Request ID, logging, rate limiting | `middleware.py` |
| **utils/** | Email, pagination, logging | `email.py`, `pagination.py`, `logging.py` |

### Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| **PostgreSQL 16** | Primary database | Persistent storage for all entities |
| **Redis 7** | Cache + rate limiting | Session cache, rate limit counters, generation progress |
| **MinIO / S3** | Object storage | CSV file uploads, generated assets |
| **Nginx** | Reverse proxy | SSL termination, rate limiting, static asset serving |
| **Sentry** | Error tracking | Production error monitoring |
| **Axiom** | Log aggregation | Structured log collection |

---

## Data Model

```
┌──────────┐     ┌──────────────┐     ┌──────────┐
│  User    │────►│  TeamMember  │◄────│  Team    │
│          │     │  (role)      │     │  (plan)  │
└────┬─────┘     └──────────────┘     └────┬─────┘
     │                                      │
     │ created_by                           │ team_id
     ▼                                      ▼
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  Tool    │────►│ ToolVersion  │     │ DataSource   │
│  (spec)  │     │ (snapshot)   │     │ (encrypted)  │
└──────────┘     └──────────────┘     └──────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│RefreshToken  │  │EmailVerif.   │  │PasswordReset │
│(hashed)      │  │(token+expiry)│  │(token+expiry)│
└──────────────┘  └──────────────┘  └──────────────┘
```

### Key Relationships

- **User ↔ Team:** Many-to-many via `TeamMember` (with role: viewer/editor/owner)
- **Team → Tool:** One-to-many (tools belong to teams)
- **Tool → ToolVersion:** One-to-many (version history with spec snapshots)
- **Team → DataSource:** One-to-many (data sources belong to teams)
- **User → RefreshToken:** One-to-many (multiple active sessions)

---

## Request Lifecycle

```
Client Request
    │
    ▼
┌──────────────┐
│    Nginx     │  ← SSL termination, rate limiting, security headers
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   FastAPI    │  ← CORS, request ID, logging middleware
│  Middleware   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Router     │  ← Path matching, Pydantic validation
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Dependency  │  ← Auth (JWT decode), RBAC (role check),
│  Injection   │     DB session, team membership
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Service    │  ← Business logic, plan enforcement
│   Layer      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  SQLAlchemy  │  ← Parameterized queries, connection pooling
│   ORM/DB     │
└──────────────┘
```

---

## Authentication Architecture

### Token Strategy

```
Access Token (15 min)     Refresh Token (7 days)
├── JWT signed (HS256)    ├── JWT signed (HS256)
├── sub: user_id          ├── sub: user_id
├── email: user_email     ├── jti: unique_id
├── type: "access"        ├── type: "refresh"
└── exp: timestamp        └── exp: timestamp
    │                         │
    │ Authorization header    │ HttpOnly cookie + body
    │ (not vulnerable to CSRF)│ (SameSite=lax)
    ▼                         ▼
```

### Refresh Token Rotation

```
Client                    Server
  │                         │
  │── POST /auth/refresh ──►│
  │   (old refresh token)   │
  │                         │── Validate old token
  │                         │── Generate new access + refresh
  │                         │── Revoke old refresh token
  │                         │── Store new refresh token hash
  │◄────────────────────────│
  │  (new access + refresh) │
  │  (new cookie set)       │
```

### RBAC Flow

```
Request with Authorization header
    │
    ▼
get_current_user()  →  Decode JWT  →  Fetch User from DB
    │
    ▼
require_role("editor")  →  Fetch TeamMember  →  Check role hierarchy
    │                                            viewer < editor < owner
    ▼
Endpoint handler  →  Use team_id from membership for data scoping
```

---

## Generation Pipeline

The AI tool generation follows a multi-stage pipeline:

```
User Prompt
    │
    ▼
┌──────────────┐
│  Classify    │  ← Determine tool type (dashboard, form, CRUD, etc.)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Clarify     │  ← Ask follow-up questions if prompt is ambiguous
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Generate    │  ← LLM generates tool spec (JSON)
│  (GPT-4o)    │     Structured output with components, data bindings
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Sanitize    │  ← Strip XSS, validate data bindings
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Validate    │  ← Schema validation, component structure
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Build       │  ← Create Tool + ToolVersion in DB
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Stream SSE  │  ← Send progress events to client
└──────────────┘
```

### Tool Spec Structure

```json
{
  "dataSources": [
    {
      "name": "sales_data",
      "type": "csv",
      "connectionId": "internal-id"
    }
  ],
  "components": [
    {
      "type": "KpiCard",
      "props": {
        "title": "Total Revenue",
        "dataSource": {"name": "sales_data", "field": "revenue"},
        "format": "currency"
      }
    },
    {
      "type": "BarChart",
      "props": {
        "title": "Revenue by Region",
        "dataSource": {"name": "sales_data"},
        "xField": "region",
        "yField": "revenue"
      }
    },
    {
      "type": "DataTable",
      "props": {
        "dataSource": {"name": "sales_data"},
        "columns": ["name", "region", "revenue", "date"],
        "sortable": true,
        "filterable": true
      }
    }
  ]
}
```

### Sandbox Rendering

Generated tools render in isolated iframes:

```
┌─────────────────────────────────────┐
│  Main App (app.deskforge.io)        │
│                                     │
│  ┌───────────────────────────────┐  │
│  │  Sandbox Iframe               │  │
│  │  (sandbox.deskforge.io)       │  │
│  │                               │  │
│  │  React app renders spec:      │  │
│  │  - KpiCard components         │  │
│  │  - BarChart / LineChart       │  │
│  │  - DataTable with filters     │  │
│  │  - Form components            │  │
│  │                               │  │
│  │  CSP: restricts script sources│  │
│  │  PostMessage: data bridge     │  │
│  └───────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```

- **Separate origin** for sandbox prevents XSS into main app
- **CSP headers** restrict script execution
- **PostMessage API** for data bridge between parent and sandbox
- **No network access** from sandbox (data provided by parent)

---

## Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────┐
│  Layer 1: Nginx                             │
│  ├── TLS 1.2/1.3                            │
│  ├── HSTS (preload)                         │
│  ├── Rate limiting (IP-based)               │
│  ├── Security headers                       │
│  └── Request size limits                    │
├─────────────────────────────────────────────┤
│  Layer 2: FastAPI Middleware                │
│  ├── CORS (origin whitelist)               │
│  ├── Rate limiting (user-based, Redis)     │
│  ├── Request ID tracking                   │
│  └── Structured logging                    │
├─────────────────────────────────────────────┤
│  Layer 3: Authentication                   │
│  ├── JWT access tokens (15 min)            │
│  ├── Refresh token rotation (7 day)        │
│  ├── Token hash storage (SHA-256)          │
│  └── Email verification                    │
├─────────────────────────────────────────────┤
│  Layer 4: Authorization                    │
│  ├── RBAC (viewer/editor/owner)            │
│  ├── Team-scoped data access               │
│  └── Plan-based feature gating             │
├─────────────────────────────────────────────┤
│  Layer 5: Data Protection                  │
│  ├── AES-256 (Fernet) credential encryption│
│  ├── bcrypt password hashing (cost 12)     │
│  ├── Parameterized SQL (no injection)      │
│  └── Input validation (Pydantic)           │
├─────────────────────────────────────────────┤
│  Layer 6: Output Security                  │
│  ├── XSS sanitizer on generated specs      │
│  ├── Public sharing data stripping         │
│  ├── Sandbox iframe isolation              │
│  └── Error message sanitization            │
└─────────────────────────────────────────────┘
```

### Data Source Credential Encryption

```
User provides DB password
    │
    ▼
encrypt_dict(config)  →  Fernet(ENCRYPTION_KEY)
    │                    AES-256-CBC + HMAC
    ▼
Encrypted string stored in DataSource.config
    │
    ▼ (on query)
decrypt_dict(config)  →  Fernet(ENCRYPTION_KEY)
    │
    ▼
Plaintext used to connect to external DB
(connection is ephemeral, not pooled)
```

---

## Deployment Architecture

### Production (Docker Compose)

```
                    Internet
                       │
                       ▼
              ┌──────────────┐
              │    Nginx     │ :80 → :443 redirect
              │   :80/:443   │ SSL termination
              └──────┬───────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
   ┌─────────────┐      ┌─────────────┐
   │  API (x2)   │      │  Web (x2)   │
   │  :8000      │      │  :3000      │
   │  1 CPU/512M │      │  0.5CPU/256M│
   └──────┬──────┘      └─────────────┘
          │
   ┌──────┴──────────────┐
   │                     │
   ▼                     ▼
┌─────────┐        ┌─────────┐
│Postgres │        │  Redis  │
│  :5432  │        │  :6379  │
│ 1 CPU   │        │ 256MB   │
└─────────┘        └─────────┘
```

### Network Isolation

- Postgres and Redis: **No external port exposure** in production
- API and Web: Only reachable via Nginx
- MinIO: Internal only (S3-compatible)
- All inter-service communication via Docker network

---

## Performance Characteristics

| Metric | Target | How |
|--------|--------|-----|
| API Response (non-gen) | < 200ms (p95) | Connection pooling, Redis cache |
| Tool Generation | < 8s (p50), < 15s (p95) | Streaming SSE, optimized prompts |
| First Contentful Paint | < 1.5s | Next.js SSG, code splitting |
| Time to Interactive | < 3s | Lazy loading, optimized bundles |
| Sandbox Render | < 2s | Pre-built component library |

---

## Technology Decisions

| Decision | Rationale |
|----------|-----------|
| **FastAPI over Django** | Native async support, OpenAPI auto-generation, dependency injection |
| **SQLAlchemy 2.0 over raw SQL** | Type safety, async support, migration tooling (Alembic) |
| **JWT over session tokens** | Stateless, works across services, no server-side session store needed |
| **Fernet (AES-256) for creds** | Simple, authenticated encryption, Python standard library support |
| **bcrypt over argon2** | Broader compatibility, well-understood, cost factor tunable |
| **Next.js App Router** | Server components, streaming, built-in API routes for future BFF |
| **Sandboxed iframes** | Security isolation for user-generated content, separate origin |
| **Redis for rate limiting** | Atomic counters, TTL support, fast reads |
| **SSE over WebSockets** | Simpler infrastructure, works with HTTP/2, sufficient for one-way streaming |
