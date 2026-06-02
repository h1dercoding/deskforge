"""Stripe API integration for DeskForge billing."""
import logging
import stripe
from typing import Optional
from uuid import UUID

from src.config import settings
from src.exceptions import StripeError

logger = logging.getLogger("deskforge.billing.stripe")

# Configure stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def _get_price_id(plan: str) -> str:
    """Map plan name to Stripe price ID."""
    price_map = {
        "starter": settings.STRIPE_STARTER_PRICE_ID,
        "pro": settings.STRIPE_PRO_PRICE_ID,
        "enterprise": settings.STRIPE_ENTERPRISE_PRICE_ID,
    }
    price_id = price_map.get(plan)
    if not price_id:
        raise StripeError(f"Unknown plan: {plan}")
    return price_id


async def create_checkout_session(
    team_id: UUID,
    plan: str,
    success_url: str,
    cancel_url: str,
    customer_email: Optional[str] = None,
    stripe_customer_id: Optional[str] = None,
) -> str:
    """Create a Stripe Checkout session for plan upgrade.

    Returns the checkout URL.
    """
    try:
        price_id = _get_price_id(plan)

        session_params = {
            "mode": "subscription",
            "payment_method_types": ["card"],
            "line_items": [
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": {
                "team_id": str(team_id),
                "plan": plan,
            },
            "subscription_data": {
                "metadata": {
                    "team_id": str(team_id),
                    "plan": plan,
                },
            },
        }

        if stripe_customer_id:
            session_params["customer"] = stripe_customer_id
        elif customer_email:
            session_params["customer_email"] = customer_email

        session = stripe.checkout.Session.create(**session_params)
        logger.info(f"Created checkout session for team {team_id}, plan {plan}")
        return session.url

    except stripe.StripeError as e:
        logger.error(f"Stripe checkout error: {e}")
        raise StripeError(str(e))


async def create_portal_session(
    stripe_customer_id: str,
    return_url: str,
) -> str:
    """Create a Stripe Customer Portal session.

    Returns the portal URL.
    """
    try:
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=return_url,
        )
        logger.info(f"Created portal session for customer {stripe_customer_id}")
        return session.url

    except stripe.StripeError as e:
        logger.error(f"Stripe portal error: {e}")
        raise StripeError(str(e))


def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
    """Verify and construct a Stripe webhook event.

    Raises StripeError if signature verification fails.
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        return event
    except stripe.SignatureVerificationError as e:
        logger.error(f"Stripe webhook signature verification failed: {e}")
        raise StripeError(f"Invalid webhook signature: {e}")
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise StripeError(f"Invalid webhook payload: {e}")


async def get_subscription(subscription_id: str) -> Optional[stripe.Subscription]:
    """Retrieve a Stripe subscription by ID."""
    try:
        return stripe.Subscription.retrieve(subscription_id)
    except stripe.StripeError as e:
        logger.error(f"Failed to retrieve subscription {subscription_id}: {e}")
        return None
