"""DeskForge API - FastAPI Application Factory."""
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.config import settings
from src.database import engine
from src.redis_client import redis_client, close_redis
from src.middleware import RequestIDMiddleware, RequestLoggingMiddleware, RateLimitMiddleware
from src.exceptions import (
    DeskForgeError,
    deskforge_error_handler,
    validation_exception_handler,
    unhandled_error_handler,
)

from src.auth.router import router as auth_router
from src.teams.router import router as teams_router
from src.tools.router import router as tools_router
from src.generate.router import router as generate_router, templates_router
from src.datasources.router import router as datasources_router
from src.billing.router import router as billing_router
from src.sharing.router import router as sharing_router
from src.audit.router import router as audit_router

logger = logging.getLogger("deskforge")

# Track startup time for health endpoint
_startup_time: float = 0.0


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers including Content-Security-Policy."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Content-Security-Policy - restrict resource loading
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Next.js needs unsafe-inline/eval
            "style-src 'self' 'unsafe-inline'",  # Tailwind needs unsafe-inline
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self' https://api.resend.com https://oauth2.googleapis.com",
            "frame-src 'self'",  # For sandbox iframes
            "frame-ancestors 'self'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Other security headers (defense-in-depth, in addition to nginx)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: connect/disconnect DB and Redis."""
    global _startup_time
    _startup_time = time.monotonic()

    # Validate critical configuration at startup (only once, not on import)
    from src.config import _validate_settings
    _validate_settings()

    logger.info("Starting DeskForge API", extra={"env": settings.APP_ENV})
    # Log only host portion of DB URL for security
    db_host = settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "unknown"
    logger.info("Database engine created", extra={"url": db_host})

    # Verify Redis connection
    try:
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")

    yield

    # Shutdown
    logger.info("Shutting down DeskForge API")
    from src.datasources.database_connector import close_all_pools
    await close_all_pools()
    await engine.dispose()
    await close_redis()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="DeskForge API",
        version="1.0.0",
        description="AI-powered internal tool generator backend",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # ── CORS ──
    # Restrict methods and headers to only what's needed
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-Id"],
        expose_headers=["X-Request-Id", "X-Response-Time", "X-RateLimit-Limit"],
    )

    # ── Security Headers (CSP, etc.) ──
    app.add_middleware(SecurityHeadersMiddleware)

    # ── Custom Middleware (order matters: last added = first executed) ──
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # ── Exception Handlers ──
    app.add_exception_handler(DeskForgeError, deskforge_error_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(PydanticValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

    # ── Routers ──
    api_prefix = "/v1"
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(teams_router, prefix=api_prefix)
    app.include_router(tools_router, prefix=api_prefix)
    app.include_router(generate_router, prefix=api_prefix)
    app.include_router(templates_router, prefix=api_prefix)
    app.include_router(datasources_router, prefix=api_prefix)
    app.include_router(billing_router, prefix=api_prefix)
    app.include_router(sharing_router, prefix=api_prefix)
    app.include_router(audit_router, prefix=api_prefix)

    # ── Health Endpoints ──

    @app.get("/health", tags=["Health"])
    async def health_check():
        """Basic liveness check."""
        uptime = time.monotonic() - _startup_time
        return {
            "status": "ok",
            "version": "1.0.0",
            "uptime": round(uptime, 2),
        }

    @app.get("/health/ready", tags=["Health"])
    async def readiness_check():
        """Readiness check (DB + Redis connectivity)."""
        checks = {"db": "ok", "redis": "ok"}

        # Check DB
        try:
            from sqlalchemy import text
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception:
            checks["db"] = "error"

        # Check Redis
        try:
            await redis_client.ping()
        except Exception:
            checks["redis"] = "error"

        all_ok = all(v == "ok" for v in checks.values())
        return {
            "status": "ready" if all_ok else "degraded",
            "checks": checks,
        }

    return app


# Module-level app instance for uvicorn
app = create_app()
