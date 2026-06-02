"""Tests for billing plan enforcement."""
import pytest
from uuid import uuid4
from httpx import AsyncClient

from src.billing.plan_enforcer import get_plan_limits, PLAN_LIMITS


def test_plan_limits_free():
    """Test free plan limits."""
    limits = get_plan_limits("free")
    assert limits["tools"] == 3
    assert limits["members"] == 3
    assert limits["datasources"] == 2
    assert limits["db_connections"] is False


def test_plan_limits_starter():
    """Test starter plan limits."""
    limits = get_plan_limits("starter")
    assert limits["tools"] is None  # unlimited
    assert limits["members"] is None  # unlimited
    assert limits["datasources"] == 5
    assert limits["db_connections"] is True


def test_plan_limits_pro():
    """Test pro plan limits."""
    limits = get_plan_limits("pro")
    assert limits["tools"] is None
    assert limits["members"] is None
    assert limits["datasources"] is None
    assert limits["db_connections"] is True


def test_plan_limits_enterprise():
    """Test enterprise plan limits."""
    limits = get_plan_limits("enterprise")
    assert limits["tools"] is None
    assert limits["members"] is None
    assert limits["datasources"] is None
    assert limits["db_connections"] is True


def test_plan_limits_unknown():
    """Test that unknown plans fall back to free."""
    limits = get_plan_limits("unknown-plan")
    assert limits == get_plan_limits("free")


def test_all_plans_have_limits():
    """Test that all expected plans are defined."""
    expected_plans = ["free", "starter", "pro", "enterprise"]
    for plan in expected_plans:
        assert plan in PLAN_LIMITS
        limits = PLAN_LIMITS[plan]
        assert "tools" in limits
        assert "members" in limits
        assert "datasources" in limits
        assert "db_connections" in limits


@pytest.mark.asyncio
async def test_get_subscription_endpoint(async_client: AsyncClient, test_user, test_team, auth_header_owner):
    """Test getting current subscription info."""
    response = await async_client.get(
        "/v1/billing/subscription",
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "plan" in data["data"]
    assert "usage" in data["data"]
    assert "limits" in data["data"]
    assert data["data"]["plan"] == "free"


@pytest.mark.asyncio
async def test_get_usage_endpoint(async_client: AsyncClient, test_user, test_team, auth_header_owner):
    """Test getting usage stats."""
    response = await async_client.get(
        "/v1/billing/usage",
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "tools" in data["data"]
    assert "members" in data["data"]
    assert "datasources" in data["data"]

    # Verify structure
    tools = data["data"]["tools"]
    assert "used" in tools
    assert "limit" in tools
    assert isinstance(tools["used"], int)


@pytest.mark.asyncio
async def test_billing_requires_owner(async_client: AsyncClient, test_editor_user, auth_header_editor):
    """Test that billing endpoints require owner role."""
    response = await async_client.get(
        "/v1/billing/subscription",
        headers=auth_header_editor,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_billing_requires_auth(async_client: AsyncClient):
    """Test that billing endpoints require authentication."""
    response = await async_client.get("/v1/billing/subscription")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_checkout_requires_valid_plan(async_client: AsyncClient, test_user, test_team, auth_header_owner):
    """Test that checkout rejects invalid plan names."""
    response = await async_client.post(
        "/v1/billing/checkout",
        json={"plan": "invalid_plan"},
        headers=auth_header_owner,
    )
    assert response.status_code == 422  # Pydantic validation


@pytest.mark.asyncio
async def test_portal_without_subscription(async_client: AsyncClient, test_user, test_team, auth_header_owner):
    """Test portal endpoint when no Stripe subscription exists."""
    response = await async_client.post(
        "/v1/billing/portal",
        headers=auth_header_owner,
    )
    # Should fail because no stripe_customer_id
    assert response.status_code == 400
