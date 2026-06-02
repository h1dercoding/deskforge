"""Pydantic models for billing endpoints."""
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class CheckoutRequest(BaseModel):
    """Request to create a Stripe checkout session."""
    plan: str = Field(pattern="^(starter|pro|enterprise)$")


class CheckoutResponse(BaseModel):
    """Response with Stripe checkout URL."""
    checkout_url: str


class PortalResponse(BaseModel):
    """Response with Stripe portal URL."""
    portal_url: str


class PlanLimitsResponse(BaseModel):
    """Plan limits info."""
    tools: Optional[int] = None  # None = unlimited
    members: Optional[int] = None
    datasources: Optional[int] = None
    db_connections: bool = True


class UsageItem(BaseModel):
    """Usage for a single resource."""
    used: int
    limit: Optional[int] = None  # None = unlimited


class UsageResponse(BaseModel):
    """Full usage stats."""
    tools: UsageItem
    members: UsageItem
    datasources: UsageItem


class SubscriptionResponse(BaseModel):
    """Current subscription info."""
    plan: str
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    usage: UsageResponse
    limits: PlanLimitsResponse
