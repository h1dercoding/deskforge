# DeskForge API Reference

**Version:** 1.0.0
**Base URL:** `https://api.deskforge.io/v1` (production) | `http://localhost:8000/v1` (development)
**OpenAPI Spec:** `GET /docs` (Swagger UI) | `GET /redoc` (ReDoc) — development only

---

## Authentication

DeskForge uses **JWT Bearer token** authentication. Access tokens are short-lived (15 min); refresh tokens are long-lived (7 days) and rotated on each use.

### Token Flow

```
┌──────────┐    POST /auth/login     ┌──────────┐
│  Client   │ ──────────────────────► │  Server   │
│           │ ◄────────────────────── │           │
│           │  { access_token,        │           │
│           │    refresh_token }      │           │
│           │                         │           │
│           │  Cookie: refresh_token  │           │
│           │  (httponly, secure)      │           │
└──────────┘                          └──────────┘

Authorization: Bearer <access_token>
```

### Making Authenticated Requests

```bash
curl -H "Authorization: Bearer <access_token>" \
     https://api.deskforge.io/v1/tools
```

### Refreshing Tokens

```bash
curl -X POST https://api.deskforge.io/v1/auth/refresh \
     -H "Content-Type: application/json" \
     -d '{"refresh_token": "<token>"}'
```

Or rely on the `refresh_token` cookie (sent automatically).

---

## Response Format

All endpoints return a consistent envelope:

### Success

```json
{
  "data": {
    "key": "value"
  }
}
```

Some list endpoints include pagination metadata:

```json
{
  "data": { "items": [...] },
  "meta": {
    "page": 1,
    "per_page": 25,
    "total": 142
  }
}
```

### Error

```json
{
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Invalid or expired access token",
    "status": 401
  }
}
```

### Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Authentication required or failed |
| 403 | Insufficient permissions |
| 404 | Resource not found |
| 409 | Conflict (e.g., email already exists) |
| 422 | Unprocessable Entity (validation) |
| 429 | Rate limit exceeded |

---

## Rate Limiting

| Endpoint Category | Limit | Scope |
|---|---|---|
| General API | 100 req/min | Per user (JWT) or per IP |
| Auth endpoints | 30 req/min | Per IP |
| Generation endpoints | 10 req/min | Per user |

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests per window

When exceeded, a 429 response is returned with `retry_after` in the error body.

---

## Endpoints

### Authentication (`/v1/auth`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/register` | No | Register with email/password |
| `POST` | `/auth/login` | No | Login with email/password |
| `POST` | `/auth/login/google` | No | Login with Google ID token |
| `POST` | `/auth/refresh` | No | Refresh access token |
| `POST` | `/auth/logout` | Yes | Revoke refresh token |
| `POST` | `/auth/verify-email` | No | Verify email with token |
| `POST` | `/auth/resend-verification` | Yes | Resend verification email |
| `POST` | `/auth/forgot-password` | No | Request password reset |
| `POST` | `/auth/reset-password` | No | Reset password with token |
| `GET` | `/auth/me` | Yes | Get current user profile |
| `PATCH` | `/auth/me` | Yes | Update profile |

#### Register

```http
POST /v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecureP@ss1",
  "name": "Jane Doe"
}
```

**Response (201):**
```json
{
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "Jane Doe",
      "email_verified": false
    },
    "tokens": {
      "access_token": "eyJ...",
      "refresh_token": "eyJ..."
    }
  }
}
```

#### Login

```http
POST /v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecureP@ss1"
}
```

**Response (200):** Same structure as register.

---

### Teams (`/v1/teams`)

| Method | Path | Role | Description |
|--------|------|------|-------------|
| `GET` | `/teams/current` | Any | Get current team |
| `PATCH` | `/teams/current` | Owner | Update team name |
| `GET` | `/teams/current/members` | Any | List team members |
| `POST` | `/teams/current/invites` | Owner | Invite a member |
| `POST` | `/teams/invites/{token}/accept` | Any | Accept invitation |
| `DELETE` | `/teams/current/members/{user_id}` | Owner | Remove member |
| `PATCH` | `/teams/current/members/{user_id}` | Owner | Change member role |

#### Invite Member

```http
POST /v1/teams/current/invites
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "colleague@example.com",
  "role": "editor"
}
```

**Roles:** `viewer` (read-only), `editor` (create/edit), `owner` (full control)

---

### Tools (`/v1/tools`)

| Method | Path | Role | Description |
|--------|------|------|-------------|
| `GET` | `/tools` | Member | List tools (paginated) |
| `GET` | `/tools/{tool_id}` | Member | Get tool with versions |
| `POST` | `/tools` | Editor+ | Create tool (requires verified email) |
| `PATCH` | `/tools/{tool_id}` | Editor+ | Update tool metadata |
| `DELETE` | `/tools/{tool_id}` | Owner | Archive tool |
| `GET` | `/tools/{tool_id}/versions` | Editor+ | List versions |
| `POST` | `/tools/{tool_id}/versions/{version_id}/restore` | Editor+ | Restore version |

#### List Tools

```http
GET /v1/tools?status=active&page=1&per_page=25
Authorization: Bearer <token>
```

**Query Parameters:**
- `status`: `active` | `draft` | `archived` | `all` (default: `active`)
- `page`: Page number (default: 1)
- `per_page`: Items per page (1-100, default: 25)

#### Create Tool

```http
POST /v1/tools
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Sales Dashboard",
  "prompt": "Create a dashboard showing revenue by region with a bar chart and KPI cards",
  "data_source_id": "uuid-optional"
}
```

---

### Generation (`/v1/generate`)

| Method | Path | Role | Description |
|--------|------|------|-------------|
| `POST` | `/generate` | Editor+ | Generate a new tool (SSE stream) |
| `POST` | `/generate/{tool_id}/iterate` | Editor+ | Iterate on existing tool (SSE stream) |
| `POST` | `/generate/clarify` | Editor+ | Continue with clarification answers (SSE stream) |
| `GET` | `/templates` | Any | List available templates |
| `GET` | `/templates/{template_id}` | Any | Get template details |

#### Generate Tool (Streaming)

```http
POST /v1/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "prompt": "Build an employee directory with search and filters",
  "data_source_id": "uuid-optional",
  "template_id": "template-id-optional"
}
```

**Response:** `text/event-stream` (Server-Sent Events)

```
data: {"type": "status", "message": "Analyzing request..."}
data: {"type": "status", "message": "Generating tool spec..."}
data: {"type": "progress", "step": "classify", "complete": true}
data: {"type": "spec", "data": {...}}
data: {"type": "complete", "tool_id": "uuid"}
```

---

### Data Sources (`/v1/datasources`)

| Method | Path | Role | Description |
|--------|------|------|-------------|
| `GET` | `/datasources` | Member | List data sources |
| `POST` | `/datasources/csv` | Editor+ | Upload CSV file |
| `POST` | `/datasources/csv/{source_id}/confirm` | Editor+ | Confirm CSV with column types |
| `GET` | `/datasources/google-sheets/auth-url` | Any | Get Google OAuth URL |
| `GET` | `/datasources/google-sheets/callback` | Editor+ | Handle Google OAuth callback |
| `POST` | `/datasources/google-sheets` | Editor+ | Connect Google Sheet |
| `POST` | `/datasources/database` | Editor+ | Connect external database |
| `POST` | `/datasources/{source_id}/test` | Member | Test connection |
| `GET` | `/datasources/{source_id}/schema` | Member | Get source schema |
| `DELETE` | `/datasources/{source_id}` | Owner | Delete data source |
| `POST` | `/datasources/{source_id}/query` | Member | Query data source |

#### Connect Database

```http
POST /v1/datasources/database
Authorization: Bearer <token>
Content-Type: application/json

{
  "type": "postgresql",
  "host": "db.example.com",
  "port": 5432,
  "database": "analytics",
  "username": "readonly_user",
  "password": "secret",
  "ssl": true,
  "readonly": true
}
```

#### Query Data Source

```http
POST /v1/datasources/{source_id}/query
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": {
    "filter": {
      "status": {"op": "eq", "value": "active"},
      "amount": {"op": "gt", "value": 100}
    },
    "sort": "created_at",
    "sort_order": "desc",
    "page": 1,
    "per_page": 50
  }
}
```

**Filter Operations:** `eq`, `contains`, `gt`, `lt`, `gte`, `lte`

---

### Billing (`/v1/billing`)

| Method | Path | Role | Description |
|--------|------|------|-------------|
| `GET` | `/billing/subscription` | Owner | Get subscription & usage |
| `POST` | `/billing/checkout` | Owner | Create Stripe checkout session |
| `POST` | `/billing/portal` | Owner | Open Stripe customer portal |
| `POST` | `/billing/webhook` | None* | Stripe webhook receiver |
| `GET` | `/billing/usage` | Owner | Get usage statistics |

*\*Webhook endpoint is unauthenticated — verified by Stripe signature.*

---

### Sharing (`/v1/sharing`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/sharing/{slug}` | Optional | Get shared tool (public or team) |
| `PATCH` | `/tools/{tool_id}/sharing` | Owner | Set visibility (public/private) |
| `POST` | `/tools/{tool_id}/sharing/regenerate` | Owner | Regenerate share link |

#### Get Shared Tool

```http
GET /v1/sharing/abc123xyz
```

No authentication required for public tools. Returns sanitized spec (internal IDs stripped).

---

### Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | No | Liveness check |
| `GET` | `/health/ready` | No | Readiness check (DB + Redis) |

---

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `AUTHENTICATION_ERROR` | 401 | Missing/invalid token |
| `AUTHORIZATION_ERROR` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Invalid request body |
| `RATE_LIMIT_ERROR` | 429 | Too many requests |
| `EMAIL_ALREADY_EXISTS` | 409 | Duplicate email |
| `INVALID_CREDENTIALS` | 401 | Wrong email/password |
| `WEAK_PASSWORD` | 422 | Password doesn't meet requirements |
| `EMAIL_NOT_VERIFIED` | 403 | Email verification required |
| `PLAN_LIMIT_EXCEEDED` | 403 | Subscription plan limit reached |
| `FEATURE_NOT_AVAILABLE` | 403 | Feature not in current plan |
| `STRIPE_ERROR` | 502 | Payment processing error |

---

## SDKs & Code Generation

The OpenAPI spec is available at `/docs` (development). Use it to generate client SDKs:

```bash
# Generate TypeScript client
npx openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-fetch \
  -o generated-client
```
