import time
import uuid
import hashlib
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.redis_client import redis_client
from src.config import settings
from src.exceptions import RateLimitError

logger = logging.getLogger("deskforge.middleware")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Adds a unique request ID to every request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs request/response details with timing."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.monotonic()
        request_id = getattr(request.state, "request_id", "unknown")

        logger.info(
            "request_started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "client": request.client.host if request.client else None,
            },
        )

        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)

        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-backed per-user rate limiting."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/health/ready"):
            return await call_next(request)

        # Identify user by JWT sub claim (user_id) or IP+UA fingerprint
        user_id = self._extract_user_id(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}:{user_id}"
        limit = settings.RATE_LIMIT_API_PER_MINUTE

        # Generation endpoints have stricter limits
        if "/generate" in request.url.path:
            key = f"rate_limit:generate:{user_id}"
            limit = settings.RATE_LIMIT_GENERATE_PER_MINUTE

        try:
            pipe = redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, 60)
            results = await pipe.execute()
            current = results[0]

            if current > limit:
                raise RateLimitError(
                    f"Rate limit exceeded. Maximum {limit} requests per minute.",
                    retry_after=60,
                )
        except Exception as e:
            if isinstance(e, RateLimitError):
                raise
            logger.warning(f"Rate limit check failed: {e}")

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        return response

    @staticmethod
    def _extract_user_id(request: Request) -> str:
        """Extract user identity for rate limiting.

        For authenticated requests: decode JWT to get the 'sub' claim (user_id).
        For unauthenticated requests: use IP + User-Agent hash.
        """
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                from src.auth.jwt import decode_access_token
                payload = decode_access_token(token)
                if payload and payload.get("sub"):
                    return payload["sub"]
            except Exception:
                pass
            # If JWT decode fails, fall through to IP-based identification

        # Unauthenticated: use IP + User-Agent hash for better uniqueness
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")
        fingerprint = hashlib.sha256(f"{client_ip}:{user_agent}".encode()).hexdigest()[:16]
        return f"ip:{fingerprint}"
