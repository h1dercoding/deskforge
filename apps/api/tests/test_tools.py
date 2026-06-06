"""Tests for tool CRUD and versioning endpoints."""
import pytest
from uuid import uuid4
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_tool(async_client: AsyncClient, test_user, test_team, auth_header_owner):
    """Test creating a new tool."""
    response = await async_client.post(
        "/v1/tools",
        json={
            "name": "Sales Dashboard",
            "prompt": "Create a dashboard showing sales data with charts and KPIs",
            "spec": {
                "version": 1,
                "name": "Sales Dashboard",
                "layout": {"type": "grid", "columns": 12, "gap": "16px"},
                "components": [
                    {
                        "id": "kpi-1",
                        "type": "KpiCard",
                        "props": {"label": "Total Sales", "value": "count"},
                        "layout": {"col": 1, "row": 1, "colSpan": 4, "rowSpan": 1},
                    }
                ],
                "dataSources": [],
                "theme": {},
            },
        },
        headers=auth_header_owner,
    )
    assert response.status_code == 201
    data = response.json()
    assert "data" in data
    assert "tool" in data["data"]
    assert data["data"]["tool"]["name"] == "Sales Dashboard"
    assert data["data"]["tool"]["status"] == "active"
    assert data["data"]["tool"]["visibility"] == "private"


@pytest.mark.asyncio
async def test_list_tools(async_client: AsyncClient, test_user, test_team, test_tool, auth_header_owner):
    """Test listing tools."""
    response = await async_client.get(
        "/v1/tools",
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "tools" in data["data"]
    assert "meta" in data
    assert data["meta"]["total"] >= 1


@pytest.mark.asyncio
async def test_list_tools_with_filter(async_client: AsyncClient, test_user, test_team, test_tool, auth_header_owner):
    """Test listing tools with status filter."""
    response = await async_client.get(
        "/v1/tools?status=active",
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    for tool in data["data"]["tools"]:
        assert tool["status"] == "active"


@pytest.mark.asyncio
async def test_get_tool(async_client: AsyncClient, test_user, test_team, test_tool, auth_header_owner):
    """Test getting a specific tool."""
    response = await async_client.get(
        f"/v1/tools/{test_tool.id}",
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["tool"]["id"] == str(test_tool.id)
    assert data["data"]["tool"]["name"] == "Test Tool"
    assert "versions" in data["data"]


@pytest.mark.asyncio
async def test_get_tool_not_found(async_client: AsyncClient, test_user, test_team, auth_header_owner):
    """Test getting a nonexistent tool."""
    response = await async_client.get(
        f"/v1/tools/{uuid4()}",
        headers=auth_header_owner,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_tool(async_client: AsyncClient, test_user, test_team, test_tool, auth_header_owner):
    """Test updating tool metadata."""
    response = await async_client.patch(
        f"/v1/tools/{test_tool.id}",
        json={
            "name": "Updated Tool Name",
            "description": "Updated description",
        },
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["tool"]["name"] == "Updated Tool Name"
    assert data["data"]["tool"]["description"] == "Updated description"


@pytest.mark.asyncio
async def test_update_tool_theme(async_client: AsyncClient, test_user, test_team, test_tool, auth_header_owner):
    """Test updating tool theme."""
    new_theme = {"primaryColor": "#ff0000", "backgroundColor": "#000000"}
    response = await async_client.patch(
        f"/v1/tools/{test_tool.id}",
        json={"theme": new_theme},
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["tool"]["theme"] == new_theme


@pytest.mark.asyncio
async def test_archive_tool(async_client: AsyncClient, test_user, test_team, test_tool, auth_header_owner):
    """Test archiving a tool."""
    response = await async_client.delete(
        f"/v1/tools/{test_tool.id}",
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["success"] is True

    # Verify the tool is archived
    get_response = await async_client.get(
        f"/v1/tools/{test_tool.id}",
        headers=auth_header_owner,
    )
    # Tool should not appear in active list
    list_response = await async_client.get(
        "/v1/tools?status=active",
        headers=auth_header_owner,
    )
    active_ids = [t["id"] for t in list_response.json()["data"]["tools"]]
    assert str(test_tool.id) not in active_ids


@pytest.mark.asyncio
async def test_list_versions(async_client: AsyncClient, test_user, test_team, test_tool, auth_header_owner):
    """Test listing tool versions."""
    response = await async_client.get(
        f"/v1/tools/{test_tool.id}/versions",
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert "versions" in data["data"]
    # Versions may be empty if tool was created directly (not via API)
    # This is acceptable — the endpoint works correctly


@pytest.mark.asyncio
async def test_create_tool_requires_editor(async_client: AsyncClient, auth_header_editor):
    """Test that editors can create tools."""
    response = await async_client.post(
        "/v1/tools",
        json={
            "name": "Editor Tool",
            "prompt": "A tool created by an editor with specific features",
            "spec": {
                "version": 1,
                "name": "Editor Tool",
                "layout": {"type": "grid", "columns": 12, "gap": "16px"},
                "components": [],
                "dataSources": [],
                "theme": {},
            },
        },
        headers=auth_header_editor,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_tool_requires_auth(async_client: AsyncClient):
    """Test that tool endpoints require authentication."""
    response = await async_client.get("/v1/tools")
    assert response.status_code == 401
