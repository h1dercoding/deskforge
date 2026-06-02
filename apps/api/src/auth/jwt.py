import jwt
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from src.config import settings
from src.models.refresh_token import RefreshToken
from src.database import async_session_factory
import sqlalchemy as sa


def create_access_token(user_id: UUID, email: str) -> str:
    """Create a JWT access token with 15-minute expiry."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: UUID) -> str:
    """Create a JWT refresh token with 7-day expiry."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate an access token. Returns payload or None."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "access":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def decode_refresh_token(token: str) -> Optional[dict]:
    """Decode and validate a refresh token. Returns payload or None."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "refresh":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def hash_token(token: str) -> str:
    """SHA-256 hash of a token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


async def store_refresh_token(user_id: UUID, token: str) -> None:
    """Store refresh token hash in database."""
    token_hash = hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    async with async_session_factory() as session:
        rt = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        session.add(rt)
        await session.commit()


async def revoke_refresh_token(token: str) -> None:
    """Revoke a refresh token."""
    token_hash = hash_token(token)
    async with async_session_factory() as session:
        await session.execute(
            sa.update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await session.commit()


async def revoke_all_refresh_tokens(user_id: UUID) -> None:
    """Revoke all refresh tokens for a user."""
    async with async_session_factory() as session:
        await session.execute(
            sa.update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await session.commit()


async def is_refresh_token_valid(token: str) -> bool:
    """Check if a refresh token is valid (not revoked, not expired)."""
    token_hash = hash_token(token)
    async with async_session_factory() as session:
        result = await session.execute(
            sa.select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none() is not None
