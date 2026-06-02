# DeskForge — AI Internal Tools Generator

**Describe it. Get it. Ship it.**

DeskForge is an AI-powered platform that generates internal tools from natural language descriptions. Describe what you need — a data dashboard, admin panel, CRUD app — and DeskForge produces a fully functional, interactive tool in under 60 seconds.

## Vision

Internal tools (admin panels, dashboards, data viewers) consume 30% of engineering time at most companies. DeskForge eliminates this by letting anyone describe a tool in plain English, connecting it to real data sources, and generating a production-ready, shareable application — no code required.

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, shadcn/ui, Zustand |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic |
| **Database** | PostgreSQL 16 |
| **Cache** | Redis 7 |
| **Object Storage** | AWS S3 / MinIO (dev) |
| **LLM** | OpenAI GPT-4o (primary), Claude 3.5 Sonnet (fallback) |
| **Auth** | Custom JWT + NextAuth.js (Google OAuth) |
| **Payments** | Stripe |
| **Email** | Resend |
| **Monitoring** | Sentry (errors), Axiom (logs) |
| **Hosting** | Vercel (frontend) + Railway (backend) |

## Architecture

Modular monolith backend (FastAPI) with a separate Next.js frontend. The two communicate via a REST API (OpenAPI 3.1) with JWT authentication. Generated tools render in sandboxed iframes with CSP security headers.

**Key Modules:** Auth, Teams, Tools, Generate, DataSources, Billing, Sharing

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.12+ (for local backend dev)
- OpenAI API key

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/deskforge.git
cd deskforge/src
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start Infrastructure

```bash
docker-compose up -d
```

This starts PostgreSQL, Redis, and MinIO. Services are available at:

| Service | URL |
|---|---|
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |
| MinIO Console | `http://localhost:9001` |
| API | `http://localhost:8000` |
| Web | `http://localhost:3000` |
| API Docs | `http://localhost:8000/docs` |

### 3. Run Database Migrations

```bash
cd apps/api
bash ../../infra/scripts/migrate.sh
```

### 4. Seed Development Data

```bash
python ../../infra/scripts/seed.py
```

### 5. Start Development Servers

**Backend:**
```bash
cd apps/api
make run
```

**Frontend:**
```bash
cd apps/web
make dev
```

## Environment Variables

See [`.env.example`](.env.example) for a complete reference. Key variables:

### Backend (apps/api)

| Variable | Description | Required |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `JWT_SECRET_KEY` | JWT signing secret (64-char hex) | Yes |
| `OPENAI_API_KEY` | OpenAI API key for generation | Yes |
| `STRIPE_SECRET_KEY` | Stripe secret key | For billing |
| `AWS_ACCESS_KEY_ID` | AWS/S3 credentials | For file uploads |

### Frontend (apps/web)

| Variable | Description | Required |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | Yes |
| `NEXTAUTH_SECRET` | NextAuth.js session secret | Yes |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | For Google login |

## Project Structure

```
src/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── src/
│   │   │   ├── auth/           # Authentication module
│   │   │   ├── teams/          # Team management
│   │   │   ├── tools/          # Tool CRUD & versioning
│   │   │   ├── generate/       # LLM generation pipeline
│   │   │   ├── datasources/    # Data source connectors
│   │   │   ├── billing/        # Stripe integration
│   │   │   ├── sharing/        # Share links
│   │   │   ├── models/         # SQLAlchemy ORM models
│   │   │   └── utils/          # Shared utilities
│   │   └── tests/
│   └── web/                    # Next.js frontend
│       └── src/
│           ├── app/            # App Router pages
│           ├── components/     # React components
│           ├── lib/            # Utilities & API client
│           ├── hooks/          # Custom React hooks
│           └── stores/         # Zustand state stores
├── packages/
│   └── shared-types/           # Shared TypeScript types
└── infra/
    ├── Dockerfile.web          # Frontend Docker build
    ├── Dockerfile.api          # Backend Docker build
    ├── nginx.conf              # Production reverse proxy
    └── scripts/
        ├── seed.py             # Database seeding
        └── migrate.sh          # Migration runner
```

## API Documentation

Full interactive API documentation is available at:

- **Development:** http://localhost:8000/docs (Swagger UI)
- **Development:** http://localhost:8000/redoc (ReDoc)
- **Production:** https://api.deskforge.io/docs

**42 endpoints** across 7 modules: Auth, Teams, Tools, Generate, DataSources, Billing, Sharing.

## Development Workflow

### Branching Strategy

- `main` — Production releases
- `develop` — Integration branch
- `feature/*` — Feature branches (PR → develop)

### Code Quality

```bash
# Backend
cd apps/api
make lint        # Run ruff linter
make format      # Auto-format with ruff
make test        # Run pytest suite

# Frontend
cd apps/web
make lint        # Run ESLint
make typecheck   # Run TypeScript compiler
make test        # Run Vitest suite
```

### Database Migrations

```bash
cd apps/api

# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Check current version
alembic current
```

## Testing

### Backend Tests

```bash
cd apps/api
make test                    # All tests
make test-unit               # Unit tests only
make test-integration        # Integration tests
make test-coverage           # With coverage report
```

### Frontend Tests

```bash
cd apps/web
make test                    # All tests
make test-watch              # Watch mode
```

### End-to-End Tests

```bash
# From project root
docker-compose -f docker-compose.yml -f docker-compose.test.yml up --abort-on-container-exit
```

## Deployment

### Production (Vercel + Railway)

**Frontend (Vercel):**
1. Connect GitHub repo to Vercel
2. Set root directory to `apps/web`
3. Configure environment variables
4. Deploy automatically on push to `main`

**Backend (Railway):**
1. Connect GitHub repo to Railway
2. Set root directory to `apps/api`
3. Add PostgreSQL and Redis services
4. Configure environment variables
5. Deploy automatically on push to `main`

### Self-Hosted (Docker)

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

The production compose file adds:
- Nginx reverse proxy
- SSL termination
- Production-optimized settings
- Health checks and restart policies

## Performance Targets

| Metric | Target |
|---|---|
| First Contentful Paint | < 1.5s |
| Time to Interactive | < 3s |
| Tool Generation (p50) | < 8s |
| Tool Generation (p95) | < 15s |
| Sandbox Render | < 2s |
| API Response (non-gen) | < 200ms (p95) |

## License

Proprietary — All rights reserved.

## Links

- [Architecture Document](../03-architecture.md)
- [PRD](../02-prd.md)
- [Market Research](../01-market-research.md)
