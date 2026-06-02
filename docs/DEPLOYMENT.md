# DeskForge Deployment Guide

**Version:** 1.0.0
**Last Updated:** 2026-06-02

---

## Deployment Options

| Method | Best For | Complexity |
|--------|----------|------------|
| **Docker Compose** | Self-hosting, staging | Low |
| **Vercel + Railway** | Production SaaS | Medium |
| **Kubernetes** | Large-scale, multi-region | High |

---

## Prerequisites

- Docker 24+ and Docker Compose v2
- Node.js 20+ (frontend builds)
- Python 3.12+ (backend)
- PostgreSQL 16+
- Redis 7+
- OpenAI API key
- Stripe account (for billing)
- Resend account (for transactional email)
- Google Cloud project (for OAuth, optional)

---

## Option 1: Docker Compose (Recommended for Self-Hosting)

### Development

```bash
# Clone and configure
git clone https://github.com/your-org/deskforge.git
cd deskforge/src
cp .env.example .env
# Edit .env with your values

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec api bash /app/infra/scripts/migrate.sh

# Seed development data (optional)
docker-compose exec api python /app/infra/scripts/seed.py
```

Services are now available:

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Web | http://localhost:3000 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |
| MinIO Console | http://localhost:9001 |

### Production

```bash
# Use production overrides
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

The production compose file (`docker-compose.prod.yml`) adds:

- **No external port exposure** for Postgres, Redis, MinIO
- **Redis password** via `REDIS_PASSWORD` env var
- **Nginx reverse proxy** with SSL termination, HSTS, security headers
- **Resource limits** per container (CPU/memory)
- **Replicas** (2x API, 2x web)
- **Always-restart** policy

#### SSL/TLS Setup

1. Place your SSL certificates in `src/infra/ssl/`:
   ```
   src/infra/ssl/
   ├── fullchain.pem
   └── privkey.pem
   ```

2. Or use Let's Encrypt with Certbot:
   ```bash
   # Install certbot
   sudo apt install certbot

   # Get certificate (stop nginx first or use webroot)
   sudo certbot certonly --standalone -d deskforge.io -d api.deskforge.io

   # Copy to infra/ssl
   sudo cp /etc/letsencrypt/live/deskforge.io/fullchain.pem src/infra/ssl/
   sudo cp /etc/letsencrypt/live/deskforge.io/privkey.pem src/infra/ssl/
   ```

3. Auto-renewal (add to crontab):
   ```bash
   0 3 * * * certbot renew --quiet && docker-compose exec nginx nginx -s reload
   ```

---

## Option 2: Vercel + Railway

### Frontend (Vercel)

1. Connect your GitHub repository to [Vercel](https://vercel.com)
2. Set **Root Directory** to `apps/web`
3. Configure environment variables:

   | Variable | Value |
   |----------|-------|
   | `NEXT_PUBLIC_API_URL` | `https://api.deskforge.io/v1` |
   | `NEXT_PUBLIC_APP_URL` | `https://app.deskforge.io` |
   | `NEXT_PUBLIC_SANDBOX_ORIGIN` | `https://sandbox.deskforge.io` |
   | `NEXTAUTH_URL` | `https://app.deskforge.io` |
   | `NEXTAUTH_SECRET` | Random 32-char string |
   | `GOOGLE_CLIENT_ID` | Google OAuth client ID |
   | `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |

4. Deploy automatically on push to `main`

### Backend (Railway)

1. Connect your GitHub repository to [Railway](https://railway.app)
2. Set **Root Directory** to `apps/api`
3. Add PostgreSQL and Redis services from Railway's marketplace
4. Configure environment variables:

   | Variable | Description |
   |----------|-------------|
   | `APP_ENV` | `production` |
   | `APP_SECRET_KEY` | Random 64-char hex string |
   | `JWT_SECRET_KEY` | Random 64-char hex string |
   | `JWT_ALGORITHM` | `HS256` |
   | `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `15` |
   | `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` |
   | `ENCRYPTION_KEY` | Random 32-byte hex string |
   | `DATABASE_URL` | Railway-provided PostgreSQL URL |
   | `REDIS_URL` | Railway-provided Redis URL |
   | `OPENAI_API_KEY` | OpenAI API key |
   | `STRIPE_SECRET_KEY` | Stripe secret key |
   | `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |
   | `STRIPE_STARTER_PRICE_ID` | Stripe price ID |
   | `STRIPE_PRO_PRICE_ID` | Stripe price ID |
   | `RESEND_API_KEY` | Resend email API key |
   | `APP_CORS_ORIGINS` | `["https://app.deskforge.io"]` |
   | `SENTRY_DSN` | Sentry DSN (optional) |

5. Deploy automatically on push to `main`

---

## Environment Variables Reference

### Required (All Environments)

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://default:pass@host:6379` |
| `JWT_SECRET_KEY` | JWT signing secret (min 32 chars) | `openssl rand -hex 32` |
| `ENCRYPTION_KEY` | Data source credential encryption key | `openssl rand -hex 32` |
| `APP_SECRET_KEY` | Application secret | `openssl rand -hex 32` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-proj-...` |

### Required (Billing)

| Variable | Description |
|----------|-------------|
| `STRIPE_SECRET_KEY` | Stripe secret API key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook endpoint signing secret |
| `STRIPE_STARTER_PRICE_ID` | Stripe Price ID for Starter plan |
| `STRIPE_PRO_PRICE_ID` | Stripe Price ID for Pro plan |
| `STRIPE_ENTERPRISE_PRICE_ID` | Stripe Price ID for Enterprise plan |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Environment name |
| `APP_PORT` | `8000` | API server port |
| `APP_HOST` | `0.0.0.0` | API server bind address |
| `APP_CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins (JSON array) |
| `DATABASE_POOL_SIZE` | `20` | Connection pool size |
| `DATABASE_MAX_OVERFLOW` | `10` | Max overflow connections |
| `DATABASE_ECHO` | `false` | Log SQL queries |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FORMAT` | `text` | Log format (`text` or `json`) |
| `SENTRY_DSN` | (empty) | Sentry error tracking DSN |
| `RATE_LIMIT_API_PER_MINUTE` | `100` | General API rate limit |
| `RATE_LIMIT_GENERATE_PER_MINUTE` | `10` | Generation endpoint rate limit |
| `RESEND_API_KEY` | (empty) | Resend email service API key |

### Generating Secrets

```bash
# Generate a 32-byte hex key (64 characters)
openssl rand -hex 32

# Generate a 16-byte hex key (32 characters)
openssl rand -hex 16

# Generate a base64 key
openssl rand -base64 32
```

---

## Database Migrations

### Running Migrations

```bash
# Docker
docker-compose exec api bash /app/infra/scripts/migrate.sh

# Local
cd apps/api
alembic upgrade head
```

### Creating Migrations

```bash
cd apps/api
alembic revision --autogenerate -m "description_of_change"
```

### Checking Status

```bash
cd apps/api
alembic current      # Current version
alembic history      # Full migration history
```

---

## Post-Deployment Checklist

### Security

- [ ] All secrets generated and set (no default/insecure values)
- [ ] `APP_ENV=production`
- [ ] SSL certificates installed and auto-renewal configured
- [ ] CORS origins restricted to production domains
- [ ] Database ports not exposed externally
- [ ] Redis password set
- [ ] Stripe webhook signature verification working
- [ ] Rate limiting tested and configured
- [ ] Security headers present (HSTS, CSP, X-Frame-Options)

### Operations

- [ ] Health checks responding (`/health`, `/health/ready`)
- [ ] Database migrations applied
- [ ] Sentry DSN configured for error tracking
- [ ] Log aggregation configured (Axiom, CloudWatch, etc.)
- [ ] Backups configured for PostgreSQL
- [ ] Monitoring alerts set up (uptime, error rate, latency)

### Functionality

- [ ] User registration and login working
- [ ] Google OAuth flow working (if enabled)
- [ ] Tool generation pipeline functional
- [ ] Data source connections working
- [ ] Stripe checkout and webhook flow tested
- [ ] Email delivery working (verification, password reset)
- [ ] Sharing/public links working
- [ ] Sandbox rendering in iframes

---

## Backup & Recovery

### PostgreSQL

```bash
# Automated daily backup (add to crontab)
0 2 * * * docker-compose exec -T postgres pg_dump -U deskforge deskforge | gzip > /backups/deskforge-$(date +\%Y\%m\%d).sql.gz

# Restore
gunzip < /backups/deskforge-20260601.sql.gz | docker-compose exec -T postgres psql -U deskforge deskforge
```

### Redis

Redis is used for caching and rate limiting only. Data loss is non-critical (sessions are JWT-based). No backup needed.

---

## Scaling

### Horizontal Scaling

- **API servers:** Increase `replicas` in `docker-compose.prod.yml` or Railway service replicas
- **Database:** Add read replicas; update `DATABASE_URL` with read endpoint
- **Redis:** Use Redis Cluster for high availability

### Vertical Scaling

- **API:** Increase CPU/memory limits in compose or Railway
- **PostgreSQL:** Increase `shared_buffers`, `work_mem` in PostgreSQL config
- **Nginx:** Increase `worker_connections` (currently 4096)

### Performance Tuning

| Parameter | Current | Tuned |
|-----------|---------|-------|
| API workers | 4 | 4-8 (per CPU core) |
| DB pool size | 20 | 20-50 |
| DB max overflow | 10 | 10-20 |
| Redis maxmemory | 256mb | 512mb-1gb |
| Nginx worker_connections | 4096 | 8192 |

---

## Troubleshooting

### API won't start

```bash
# Check logs
docker-compose logs api

# Common causes:
# - Missing required environment variables
# - Database not ready
# - Redis not reachable
# - Insecure secret key detected
```

### Database connection errors

```bash
# Verify database is running
docker-compose exec postgres pg_isready -U deskforge

# Check connection from API container
docker-compose exec api python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('postgresql+asyncpg://deskforge:password@postgres:5432/deskforge'))"
```

### Rate limiting not working

```bash
# Check Redis connectivity
docker-compose exec redis redis-cli ping

# Check rate limit keys
docker-compose exec redis redis-cli KEYS "rate_limit:*"
```

### Stripe webhooks failing

```bash
# Verify webhook secret matches Stripe dashboard
# Test with Stripe CLI
stripe listen --forward-to localhost:8000/v1/billing/webhook
```
