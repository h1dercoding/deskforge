"""Billing API endpoints."""
import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db, get_current_user, require_role, get_team_membership
from src.models.user import User
from src.models.team_member import TeamMember
from src.teams.service import get_team_for_user
from src.config import settings

from src.billing.schemas import (
    CheckoutRequest,
    CheckoutResponse,
    PortalResponse,
    SubscriptionResponse,
    UsageResponse,
    UsageItem,
    PlanLimitsResponse,
)
from src.billing.plan_enforcer import get_plan_limits, get_usage, get_team_plan
from src.billing.stripe_service import create_checkout_session, create_portal_session, construct_webhook_event
from src.billing.webhook_handler import process_webhook_event

logger = logging.getLogger("deskforge.billing")

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.get("/subscription", response_model=dict)
async def get_subscription_endpoint(
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("owner")),
):
    """Get current subscription, plan, and usage."""
    current_user, membership = auth_data
    team, _ = await get_team_for_user(db, current_user.id)

    plan = team.plan or "free"
    limits = get_plan_limits(plan)
    usage = await get_usage(membership.team_id)

    return {
        "data": SubscriptionResponse(
            plan=plan,
            stripe_customer_id=team.stripe_customer_id,
            stripe_subscription_id=team.stripe_subscription_id,
            usage=UsageResponse(
                tools=UsageItem(used=usage["tools"], limit=limits["tools"]),
                members=UsageItem(used=usage["members"], limit=limits["members"]),
                datasources=UsageItem(used=usage["datasources"], limit=limits["datasources"]),
            ),
            limits=PlanLimitsResponse(**limits),
        )
    }


@router.post("/checkout", response_model=dict)
async def create_checkout_endpoint(
    body: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("owner")),
):
    """Create a Stripe checkout session for plan upgrade."""
    current_user, membership = auth_data
    team, _ = await get_team_for_user(db, current_user.id)

    app_url = settings.app_url
    success_url = f"{app_url}/team/billing?checkout=success"
    cancel_url = f"{app_url}/team/billing?checkout=cancelled"

    checkout_url = await create_checkout_session(
        team_id=membership.team_id,
        plan=body.plan,
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=current_user.email,
        stripe_customer_id=team.stripe_customer_id,
    )

    return {"data": CheckoutResponse(checkout_url=checkout_url)}


@router.post("/portal", response_model=dict)
async def open_portal_endpoint(
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("owner")),
):
    """Open Stripe customer portal for subscription management."""
    current_user, membership = auth_data
    team, _ = await get_team_for_user(db, current_user.id)

    if not team.stripe_customer_id:
        from src.exceptions import ValidationError
        raise ValidationError("No billing account found. Please subscribe to a plan first.")

    return_url = f"{settings.app_url}/team/billing"
    portal_url = await create_portal_session(
        stripe_customer_id=team.stripe_customer_id,
        return_url=return_url,
    )

    return {"data": PortalResponse(portal_url=portal_url)}


@router.post("/webhook", status_code=200)
async def stripe_webhook_endpoint(request: Request):
    """Handle Stripe webhook events.

    Verifies the webhook signature and processes the event.
    No authentication required - verified by Stripe signature.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        from src.exceptions import ValidationError
        raise ValidationError("Missing stripe-signature header")

    event = construct_webhook_event(payload, sig_header)
    event_type = event["type"]
    event_data = event

    logger.info(f"Processing Stripe webhook: {event_type}")
    await process_webhook_event(event_type, event_data)

    return {"received": True}


@router.get("/usage", response_model=dict)
async def get_usage_endpoint(
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("owner")),
):
    """Get usage stats for the current team."""
    current_user, membership = auth_data
    team, _ = await get_team_for_user(db, current_user.id)

    plan = team.plan or "free"
    limits = get_plan_limits(plan)
    usage = await get_usage(membership.team_id)

    return {
        "data": UsageResponse(
            tools=UsageItem(used=usage["tools"], limit=limits["tools"]),
            members=UsageItem(used=usage["members"], limit=limits["members"]),
            datasources=UsageItem(used=usage["datasources"], limit=limits["datasources"]),
        )
    }
