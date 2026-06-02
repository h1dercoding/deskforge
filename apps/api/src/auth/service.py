import secrets
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.models.email_verification import EmailVerification
from src.models.password_reset import PasswordReset
from src.auth.password import hash_password, verify_password, validate_password_strength
from src.auth.jwt import (
    create_access_token,
    create_refresh_token,
    store_refresh_token,
    revoke_refresh_token,
    revoke_all_refresh_tokens,
    is_refresh_token_valid,
)
from src.auth.oauth import verify_google_id_token
from src.utils.email import send_verification_email, send_password_reset_email, send_welcome_email
from src.exceptions import (
    InvalidCredentialsError,
    EmailAlreadyExistsError,
    WeakPasswordError,
    EmailNotVerifiedError,
    TokenInvalidError,
    UserNotFoundError,
    AuthenticationError,
)

logger = logging.getLogger("deskforge.auth")

VERIFICATION_TOKEN_EXPIRY_HOURS = 24
PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 1


async def register_user(db: AsyncSession, email: str, password: str, name: str) -> dict:
    """Register a new user with email/password."""
    email = email.lower().strip()

    existing = await db.execute(sa.select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise EmailAlreadyExistsError()

    if not validate_password_strength(password):
        raise WeakPasswordError()

    user = User(
        email=email,
        password_hash=hash_password(password),
        name=name.strip(),
        auth_provider="local",
        email_verified=False,
    )
    db.add(user)
    await db.flush()

    # Create email verification token
    token = secrets.token_urlsafe(32)
    verification = EmailVerification(
        user_id=user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_TOKEN_EXPIRY_HOURS),
    )
    db.add(verification)
    await db.commit()
    await db.refresh(user)

    # Send verification email (non-blocking)
    try:
        await send_verification_email(email=email, name=name, token=token)
    except Exception as e:
        logger.warning(f"Failed to send verification email: {e}")

    # Auto-create team
    from src.teams.service import create_team_for_user
    await create_team_for_user(db, user)

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)
    await store_refresh_token(user.id, refresh_token)

    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


async def login_user(db: AsyncSession, email: str, password: str) -> dict:
    """Authenticate user with email/password."""
    email = email.lower().strip()

    result = await db.execute(sa.select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None or user.password_hash is None:
        raise InvalidCredentialsError()

    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)
    await store_refresh_token(user.id, refresh_token)

    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


async def login_with_google(db: AsyncSession, id_token: str) -> dict:
    """Authenticate or register user via Google OAuth."""
    google_data = await verify_google_id_token(id_token)
    if not google_data:
        raise AuthenticationError("Invalid Google token.", 1100)

    email = google_data["email"]
    result = await db.execute(sa.select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        # Create new user from Google data
        user = User(
            email=email,
            name=google_data["name"],
            avatar_url=google_data.get("avatar_url"),
            email_verified=google_data.get("email_verified", True),
            auth_provider="google",
            google_id=google_data["google_id"],
        )
        db.add(user)
        await db.flush()

        from src.teams.service import create_team_for_user
        await create_team_for_user(db, user)
        await db.commit()
        await db.refresh(user)

        try:
            await send_welcome_email(email=email, name=google_data["name"])
        except Exception as e:
            logger.warning(f"Failed to send welcome email: {e}")
    else:
        # Link Google account if not already linked
        if user.google_id is None:
            user.google_id = google_data["google_id"]
            user.auth_provider = "google"
            if not user.avatar_url and google_data.get("avatar_url"):
                user.avatar_url = google_data["avatar_url"]
            await db.commit()
            await db.refresh(user)

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)
    await store_refresh_token(user.id, refresh_token)

    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


async def refresh_access_token(db: AsyncSession, refresh_token_str: str) -> dict:
    """Refresh an access token using a valid refresh token."""
    if not await is_refresh_token_valid(refresh_token_str):
        raise AuthenticationError("Invalid or expired refresh token.", 1101)

    from src.auth.jwt import decode_refresh_token
    payload = decode_refresh_token(refresh_token_str)
    if payload is None:
        raise AuthenticationError("Invalid refresh token.", 1102)

    user_id = UUID(payload["sub"])
    result = await db.execute(sa.select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise UserNotFoundError()

    new_access_token = create_access_token(user.id, user.email)
    new_refresh_token = create_refresh_token(user.id)
    await store_refresh_token(user.id, new_refresh_token)

    # Revoke old refresh token
    await revoke_refresh_token(refresh_token_str)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
    }


async def logout_user(refresh_token_str: str) -> None:
    """Revoke a refresh token (logout)."""
    await revoke_refresh_token(refresh_token_str)


async def verify_email(db: AsyncSession, token: str) -> None:
    """Verify user's email with token."""
    result = await db.execute(
        sa.select(EmailVerification).where(
            EmailVerification.token == token,
            EmailVerification.used_at.is_(None),
            EmailVerification.expires_at > datetime.now(timezone.utc),
        )
    )
    verification = result.scalar_one_or_none()
    if verification is None:
        raise TokenInvalidError()

    verification.used_at = datetime.now(timezone.utc)

    user_result = await db.execute(sa.select(User).where(User.id == verification.user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise UserNotFoundError()

    user.email_verified = True
    await db.commit()


async def resend_verification(db: AsyncSession, user_id: UUID) -> None:
    """Resend email verification."""
    result = await db.execute(sa.select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise UserNotFoundError()

    if user.email_verified:
        return

    token = secrets.token_urlsafe(32)
    verification = EmailVerification(
        user_id=user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_TOKEN_EXPIRY_HOURS),
    )
    db.add(verification)
    await db.commit()

    try:
        await send_verification_email(email=user.email, name=user.name, token=token)
    except Exception as e:
        logger.warning(f"Failed to send verification email: {e}")


async def forgot_password(db: AsyncSession, email: str) -> None:
    """Send password reset email if user exists."""
    email = email.lower().strip()
    result = await db.execute(sa.select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        return  # Don't reveal if email exists

    token = secrets.token_urlsafe(32)
    reset = PasswordReset(
        user_id=user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=PASSWORD_RESET_TOKEN_EXPIRY_HOURS),
    )
    db.add(reset)
    await db.commit()

    try:
        await send_password_reset_email(email=email, name=user.name, token=token)
    except Exception as e:
        logger.warning(f"Failed to send password reset email: {e}")


async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
    """Reset password using a valid token."""
    if not validate_password_strength(new_password):
        raise WeakPasswordError()

    result = await db.execute(
        sa.select(PasswordReset).where(
            PasswordReset.token == token,
            PasswordReset.used_at.is_(None),
            PasswordReset.expires_at > datetime.now(timezone.utc),
        )
    )
    reset = result.scalar_one_or_none()
    if reset is None:
        raise TokenInvalidError()

    reset.used_at = datetime.now(timezone.utc)

    user_result = await db.execute(sa.select(User).where(User.id == reset.user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise UserNotFoundError()

    user.password_hash = hash_password(new_password)
    await db.commit()

    await revoke_all_refresh_tokens(user.id)


async def update_profile(db: AsyncSession, user: User, **kwargs) -> User:
    """Update user profile."""
    if "name" in kwargs and kwargs["name"]:
        user.name = kwargs["name"]
    if "email" in kwargs and kwargs["email"]:
        new_email = kwargs["email"].lower().strip()
        if new_email != user.email:
            existing = await db.execute(sa.select(User).where(User.email == new_email))
            if existing.scalar_one_or_none():
                raise EmailAlreadyExistsError()
            user.email = new_email
            user.email_verified = False
    if "avatar_url" in kwargs:
        user.avatar_url = kwargs["avatar_url"]

    await db.commit()
    await db.refresh(user)
    return user
