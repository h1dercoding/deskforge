"""Handle Stripe webhook events for plan management."""
import logging
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session_factory
from src.models.team import Team
from src.exceptions import StripeError

logger = logging.getLogger("deskforge.billing.webhooks")


async def handle_checkout_completed(event_data: dict) -> None:
    """Handle checkout.session.completed event.

    Activates the subscription and updates the team's plan.
    """
    session = event_data.get("data", {}).get("object", {})
    metadata = session.get("metadata", {})
    team_id = metadata.get("team_id")
    plan = metadata.get("plan")
    subscription_id = session.get("subscription")
    customer_id = session.get("customer")

    if not team_id or not plan:
        logger.error(f"Missing metadata in checkout.session.completed: {metadata}")
        return

    async with async_session_factory() as db:
        result = await db.execute(
            sa.select(Team).where(Team.id == UUID(team_id))
        )
        team = result.scalar_one_or_none()
        if not team:
            logger.error(f"Team {team_id} not found for checkout completion")
            return

        team.plan = plan
        team.stripe_customer_id = customer_id
        team.stripe_subscription_id = subscription_id
        await db.commit()

    logger.info(f"Activated {plan} plan for team {team_id}")


async def handle_subscription_updated(event_data: dict) -> None:
    """Handle customer.subscription.updated event.

    Updates the team's plan if it changed.
    """
    subscription = event_data.get("data", {}).get("object", {})
    metadata = subscription.get("metadata", {})
    team_id = metadata.get("team_id")
    plan = metadata.get("plan")
    subscription_id = subscription.get("id")
    status = subscription.get("status")

    if not team_id:
        logger.warning(f"No team_id in subscription update: {subscription_id}")
        return

    async with async_session_factory() as db:
        result = await db.execute(
            sa.select(Team).where(Team.id == UUID(team_id))
        )
        team = result.scalar_one_or_none()
        if not team:
            logger.error(f"Team {team_id} not found for subscription update")
            return

        if status == "active" and plan:
            team.plan = plan
        elif status in ("canceled", "unpaid", "past_due"):
            # Downgrade to free on cancellation or payment issues
            team.plan = "free"
            team.stripe_subscription_id = None

        team.stripe_subscription_id = subscription_id
        await db.commit()

    logger.info(f"Updated subscription for team {team_id}: status={status}, plan={plan}")


async def handle_subscription_deleted(event_data: dict) -> None:
    """Handle customer.subscription.deleted event.

    Downgrades the team to the free plan.
    """
    subscription = event_data.get("data", {}).get("object", {})
    metadata = subscription.get("metadata", {})
    team_id = metadata.get("team_id")

    if not team_id:
        # Try to find by subscription ID
        subscription_id = subscription.get("id")
        if subscription_id:
            async with async_session_factory() as db:
                result = await db.execute(
                    sa.select(Team).where(Team.stripe_subscription_id == subscription_id)
                )
                team = result.scalar_one_or_none()
                if team:
                    team.plan = "free"
                    team.stripe_subscription_id = None
                    await db.commit()
                    logger.info(f"Downgraded team {team.id} to free (subscription deleted)")
        return

    async with async_session_factory() as db:
        result = await db.execute(
            sa.select(Team).where(Team.id == UUID(team_id))
        )
        team = result.scalar_one_or_none()
        if not team:
            logger.error(f"Team {team_id} not found for subscription deletion")
            return

        team.plan = "free"
        team.stripe_subscription_id = None
        await db.commit()

    logger.info(f"Downgraded team {team_id} to free (subscription deleted)")


async def handle_invoice_payment_failed(event_data: dict) -> None:
    """Handle invoice.payment_failed event.

    Logs the failure and could trigger email notification.
    """
    invoice = event_data.get("data", {}).get("object", {})
    customer_id = invoice.get("customer")
    subscription_id = invoice.get("subscription")
    attempt_count = invoice.get("attempt_count", 0)

    logger.warning(
        f"Invoice payment failed: customer={customer_id}, "
        f"subscription={subscription_id}, attempts={attempt_count}"
    )

    # Find the team by subscription ID
    if subscription_id:
        async with async_session_factory() as db:
            result = await db.execute(
                sa.select(Team).where(Team.stripe_subscription_id == subscription_id)
            )
            team = result.scalar_one_or_none()
            if team:
                # After 3 failed attempts, downgrade to free
                if attempt_count >= 3:
                    team.plan = "free"
                    team.stripe_subscription_id = None
                    await db.commit()
                    logger.info(f"Downgraded team {team.id} after {attempt_count} failed payments")

                # TODO: Send email notification about failed payment
                logger.info(f"Payment failure notification needed for team {team.id}")


# Event handler map
WEBHOOK_HANDLERS = {
    "checkout.session.completed": handle_checkout_completed,
    "customer.subscription.updated": handle_subscription_updated,
    "customer.subscription.deleted": handle_subscription_deleted,
    "invoice.payment_failed": handle_invoice_payment_failed,
}


async def process_webhook_event(event_type: str, event_data: dict) -> None:
    """Process a Stripe webhook event."""
    handler = WEBHOOK_HANDLERS.get(event_type)
    if handler:
        await handler(event_data)
    else:
        logger.info(f"Unhandled Stripe event type: {event_type}")
