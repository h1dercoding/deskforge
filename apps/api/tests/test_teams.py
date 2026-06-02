"""Tests for team endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_current_team(async_client: AsyncClient, test_user, test_team, auth_header_owner):
    """Test getting current team."""
    response = await async_client.get(
        "/v1/teams/current",
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "team" in data["data"]
    assert data["data"]["team"]["name"] == "Test Team"


@pytest.mark.asyncio
async def test_update_team(async_client: AsyncClient, test_user, test_team, auth_header_owner):
    """Test updating team name."""
    response = await async_client.patch(
        "/v1/teams/current",
        json={"name": "Updated Team"},
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["team"]["name"] == "Updated Team"


@pytest.mark.asyncio
async def test_update_team_requires_owner(async_client: AsyncClient, test_editor_user, auth_header_editor):
    """Test that only owner can update team."""
    response = await async_client.patch(
        "/v1/teams/current",
        json={"name": "Hacker Team"},
        headers=auth_header_editor,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_members(async_client: AsyncClient, test_user, test_team, auth_header_owner):
    """Test listing team members."""
    response = await async_client.get(
        "/v1/teams/current/members",
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "members" in data["data"]
    assert len(data["data"]["members"]) >= 1
    # Verify owner is in the list
    owner_found = any(m["role"] == "owner" for m in data["data"]["members"])
    assert owner_found


@pytest.mark.asyncio
async def test_invite_member(async_client: AsyncClient, test_user, test_team, auth_header_owner):
    """Test inviting a new member."""
    response = await async_client.post(
        "/v1/teams/current/invites",
        json={"email": "newmember@example.com", "role": "editor"},
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "invite" in data["data"]
    assert data["data"]["invite"]["email"] == "newmember@example.com"
    assert data["data"]["invite"]["role"] == "editor"


@pytest.mark.asyncio
async def test_invite_requires_owner(async_client: AsyncClient, test_editor_user, auth_header_editor):
    """Test that only owner can invite members."""
    response = await async_client.post(
        "/v1/teams/current/invites",
        json={"email": "someone@example.com", "role": "viewer"},
        headers=auth_header_editor,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_change_member_role(async_client: AsyncClient, test_editor_user, test_team, auth_header_owner):
    """Test changing a member's role."""
    response = await async_client.patch(
        f"/v1/teams/current/members/{test_editor_user.id}",
        json={"role": "viewer"},
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["member"]["role"] == "viewer"


@pytest.mark.asyncio
async def test_remove_member(async_client: AsyncClient, test_editor_user, test_team, auth_header_owner):
    """Test removing a team member."""
    response = await async_client.delete(
        f"/v1/teams/current/members/{test_editor_user.id}",
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["success"] is True


@pytest.mark.asyncio
async def test_team_requires_auth(async_client: AsyncClient):
    """Test that team endpoints require authentication."""
    response = await async_client.get("/v1/teams/current")
    assert response.status_code == 401
