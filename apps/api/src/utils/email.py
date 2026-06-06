"""Email sending utilities using Resend API."""
import logging
from typing import Optional

import httpx

from src.config import settings

logger = logging.getLogger("deskforge.utils.email")

RESEND_API_URL = "https://api.resend.com/emails"


async def _send_email(
    to: str,
    subject: str,
    html: str,
    from_email: Optional[str] = None,
) -> bool:
    """Send an email using the Resend API.

    Returns True if sent successfully, False otherwise.
    """
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set, skipping email send")
        return False

    sender = from_email or settings.EMAIL_FROM

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": sender,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                logger.info(f"Email sent to {to}: {subject}")
                return True
            else:
                logger.error(
                    f"Failed to send email to {to}: {response.status_code} {response.text}"
                )
                return False

    except Exception as e:
        logger.error(f"Email send error for {to}: {e}")
        return False


async def send_verification_email(email: str, token: str, name: str = "") -> bool:
    """Send email verification link."""
    verify_url = f"{settings.app_url}/verify?token={token}"
    greeting = f"Hi {name}," if name else "Hi,"

    html = f"""
    <h2>Welcome to DeskForge!</h2>
    <p>{greeting}</p>
    <p>Please verify your email address by clicking the link below:</p>
    <p><a href="{verify_url}">Verify Email Address</a></p>
    <p>This link will expire in 24 hours.</p>
    <p>If you didn't create an account, you can safely ignore this email.</p>
    """

    return await _send_email(
        to=email,
        subject="Verify your DeskForge email",
        html=html,
    )


async def send_invite_email(
    email: str,
    team_name: str,
    role: str,
    token: str,
) -> bool:
    """Send team invitation email."""
    invite_url = f"{settings.app_url}/invite?token={token}"

    html = f"""
    <h2>You've been invited to DeskForge!</h2>
    <p>You've been invited to join <strong>{team_name}</strong> as a <strong>{role}</strong>.</p>
    <p><a href="{invite_url}">Accept Invitation</a></p>
    <p>This invitation will expire in 7 days.</p>
    <p>If you don't have a DeskForge account, you'll be prompted to create one.</p>
    """

    return await _send_email(
        to=email,
        subject=f"Join {team_name} on DeskForge",
        html=html,
    )


async def send_password_reset_email(email: str, token: str, name: str = "") -> bool:
    """Send password reset link."""
    reset_url = f"{settings.app_url}/reset-password?token={token}"
    greeting = f"Hi {name}," if name else "Hi,"

    html = f"""
    <h2>Reset your DeskForge password</h2>
    <p>{greeting}</p>
    <p>You requested a password reset. Click the link below to set a new password:</p>
    <p><a href="{reset_url}">Reset Password</a></p>
    <p>This link will expire in 1 hour.</p>
    <p>If you didn't request a password reset, you can safely ignore this email.</p>
    """

    return await _send_email(
        to=email,
        subject="Reset your DeskForge password",
        html=html,
    )


async def send_payment_failed_email(email: str, team_name: str) -> bool:
    """Send payment failure notification."""
    billing_url = f"{settings.app_url}/team/billing"

    html = f"""
    <h2>Payment Failed</h2>
    <p>We were unable to process the payment for your <strong>{team_name}</strong> subscription.</p>
    <p>Please update your payment information to continue using DeskForge Pro features:</p>
    <p><a href="{billing_url}">Update Payment Method</a></p>
    <p>If no action is taken, your account will be downgraded to the free plan.</p>
    """

    return await _send_email(
        to=email,
        subject="DeskForge Payment Failed - Action Required",
        html=html,
    )


async def send_welcome_email(email: str, name: str = "") -> bool:
    """Send welcome email to new Google OAuth users."""
    greeting = f"Hi {name}," if name else "Hi,"

    html = f"""
    <h2>Welcome to DeskForge!</h2>
    <p>{greeting}</p>
    <p>Your account has been created successfully with Google Sign-In.</p>
    <p>Start building internal tools by describing what you need in plain English.</p>
    <p><a href="{settings.app_url}/dashboard">Go to Dashboard</a></p>
    """

    return await _send_email(
        to=email,
        subject="Welcome to DeskForge!",
        html=html,
    )


# Alias for backward compatibility
send_team_invite_email = send_invite_email
