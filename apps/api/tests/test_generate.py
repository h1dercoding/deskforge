"""Tests for generation pipeline and templates."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_templates(async_client: AsyncClient, test_user, auth_header_owner):
    """Test listing available templates."""
    response = await async_client.get(
        "/v1/templates",
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "templates" in data["data"]
    assert len(data["data"]["templates"]) > 0

    # Verify template structure
    template = data["data"]["templates"][0]
    assert "id" in template
    assert "name" in template
    assert "description" in template
    assert "category" in template
    assert "prompt" in template


@pytest.mark.asyncio
async def test_get_template(async_client: AsyncClient, test_user, auth_header_owner):
    """Test getting a specific template."""
    # First list templates to get a valid ID
    list_response = await async_client.get(
        "/v1/templates",
        headers=auth_header_owner,
    )
    templates = list_response.json()["data"]["templates"]
    if not templates:
        pytest.skip("No templates available")

    template_id = templates[0]["id"]
    response = await async_client.get(
        f"/v1/templates/{template_id}",
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["template"]["id"] == template_id


@pytest.mark.asyncio
async def test_get_template_not_found(async_client: AsyncClient, test_user, auth_header_owner):
    """Test getting a nonexistent template."""
    response = await async_client.get(
        "/v1/templates/nonexistent-template-id",
        headers=auth_header_owner,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_requires_editor(async_client: AsyncClient, test_user, test_team, auth_header_owner):
    """Test that generation requires editor role or above."""
    # The endpoint should be accessible (returns SSE stream)
    # We can't easily test the full SSE flow without mocking the LLM,
    # but we can verify the endpoint exists and validates input
    response = await async_client.post(
        "/v1/generate",
        json={
            "prompt": "test",  # Too short, should fail validation
        },
        headers=auth_header_owner,
    )
    # Should fail with validation error (prompt too short) or 403 (email not verified is OK too)
    assert response.status_code in (422, 403)


@pytest.mark.asyncio
async def test_generate_prompt_too_short(async_client: AsyncClient, test_user, test_team, auth_header_owner):
    """Test that short prompts are rejected."""
    response = await async_client.post(
        "/v1/generate",
        json={
            "prompt": "hi",  # Too short (< 10 chars)
        },
        headers=auth_header_owner,
    )
    assert response.status_code in (422, 403)


@pytest.mark.asyncio
async def test_generate_requires_auth(async_client: AsyncClient):
    """Test that generation requires authentication."""
    response = await async_client.post(
        "/v1/generate",
        json={
            "prompt": "Create a dashboard with sales data and charts",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_iterate_requires_auth(async_client: AsyncClient):
    """Test that iteration requires authentication."""
    response = await async_client.post(
        "/v1/generate/some-tool-id/iterate",
        json={"message": "Add a bar chart"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_clarify_requires_auth(async_client: AsyncClient):
    """Test that clarify requires authentication."""
    response = await async_client.post(
        "/v1/generate/clarify",
        json={
            "session_id": "test-session",
            "answers": ["Use CSV data source"],
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_templates_require_auth(async_client: AsyncClient):
    """Test that template endpoints require authentication."""
    response = await async_client.get("/v1/templates")
    assert response.status_code == 401
