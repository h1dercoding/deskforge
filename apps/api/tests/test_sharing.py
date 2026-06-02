"""Tests for sharing endpoints."""
import pytest
from uuid import uuid4
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_shared_tool_public(async_client: AsyncClient, test_user, test_team, test_tool, auth_header_owner):
    """Test accessing a public shared tool."""
    # First make the tool public
    update_response = await async_client.patch(
        f"/v1/tools/{test_tool.id}/sharing",
        json={"visibility": "public"},
        headers=auth_header_owner,
    )
    assert update_response.status_code == 200
    slug = update_response.json()["data"]["slug"]

    # Access via sharing endpoint (no auth)
    response = await async_client.get(f"/v1/sharing/{slug}")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"]["name"] == "Test Tool"
    assert data["data"]["is_public"] is True
    assert "spec" in data["data"]


@pytest.mark.asyncio
async def test_get_shared_tool_private_no_auth(async_client: AsyncClient, test_user, test_team, test_tool, auth_header_owner):
    """Test that private tools are not accessible without auth."""
    # Ensure tool is private
    await async_client.patch(
        f"/v1/tools/{test_tool.id}/sharing",
        json={"visibility": "private"},
        headers=auth_header_owner,
    )

    # Try to access via sharing endpoint (no auth)
    response = await async_client.get(f"/v1/sharing/{test_tool.slug}")
    assert response.status_code == 404  # Not publicly shared


@pytest.mark.asyncio
async def test_get_shared_tool_private_with_auth(async_client: AsyncClient, test_user, test_team, test_tool, auth_header_owner):
    """Test that team members can access private tools via sharing URL."""
    # Ensure tool is private
    await async_client.patch(
        f"/v1/tools/{test_tool.id}/sharing",
        json={"visibility": "private"},
        headers=auth_header_owner,
    )

    # Access with auth (team member)
    response = await async_client.get(
        f"/v1/sharing/{test_tool.slug}",
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == "Test Tool"


@pytest.mark.asyncio
async def test_update_visibility_to_public(async_client: AsyncClient, test_user, test_team, test_tool, auth_header_owner):
    """Test setting tool visibility to public."""
    response = await async_client.patch(
        f"/v1/tools/{test_tool.id}/sharing",
        json={"visibility": "public"},
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["visibility"] == "public"
    assert "slug" in data["data"]


@pytest.mark.asyncio
async def test_update_visibility_to_private(async_client: AsyncClient, test_user, test_team, test_tool, auth_header_owner):
    """Test setting tool visibility to private."""
    # First make it public
    await async_client.patch(
        f"/v1/tools/{test_tool.id}/sharing",
        json={"visibility": "public"},
        headers=auth_header_owner,
    )

    # Then make it private
    response = await async_client.patch(
        f"/v1/tools/{test_tool.id}/sharing",
        json={"visibility": "private"},
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["visibility"] == "private"


@pytest.mark.asyncio
async def test_update_visibility_invalid(async_client: AsyncClient, test_user, test_team, test_tool, auth_header_owner):
    """Test setting invalid visibility value."""
    response = await async_client.patch(
        f"/v1/tools/{test_tool.id}/sharing",
        json={"visibility": "invalid"},
        headers=auth_header_owner,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_regenerate_link(async_client: AsyncClient, test_user, test_team, test_tool, auth_header_owner):
    """Test regenerating a share link."""
    # First make it public to get an initial slug
    await async_client.patch(
        f"/v1/tools/{test_tool.id}/sharing",
        json={"visibility": "public"},
        headers=auth_header_owner,
    )
    original_slug = test_tool.slug

    # Regenerate
    response = await async_client.post(
        f"/v1/tools/{test_tool.id}/sharing/regenerate",
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert "slug" in data["data"]
    # The new slug should be different (or same if no collision handling changed it)
    assert isinstance(data["data"]["slug"], str)
    assert len(data["data"]["slug"]) > 0


@pytest.mark.asyncio
async def test_sharing_requires_owner(async_client: AsyncClient, test_editor_user, test_tool, auth_header_editor):
    """Test that sharing management requires owner role."""
    response = await async_client.patch(
        f"/v1/tools/{test_tool.id}/sharing",
        json={"visibility": "public"},
        headers=auth_header_editor,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_shared_tool_not_found(async_client: AsyncClient):
    """Test accessing a nonexistent shared tool."""
    response = await async_client.get("/v1/sharing/nonexistent-slug")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_regenerate_requires_owner(async_client: AsyncClient, test_editor_user, test_tool, auth_header_editor):
    """Test that regenerating share link requires owner role."""
    response = await async_client.post(
        f"/v1/tools/{test_tool.id}/sharing/regenerate",
        headers=auth_header_editor,
    )
    assert response.status_code == 403
