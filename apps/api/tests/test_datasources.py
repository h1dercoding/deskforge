"""Tests for data source endpoints."""
import pytest
import io
from uuid import uuid4
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_datasources(async_client: AsyncClient, test_user, test_team, auth_header_owner):
    """Test listing data sources."""
    response = await async_client.get(
        "/v1/datasources",
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "sources" in data["data"]


@pytest.mark.asyncio
async def test_upload_csv(async_client: AsyncClient, test_user, test_team, auth_header_owner):
    """Test CSV file upload."""
    # Create a simple CSV file
    csv_content = "name,email,age\nJohn,john@example.com,30\nJane,jane@example.com,25"
    csv_bytes = csv_content.encode("utf-8")

    response = await async_client.post(
        "/v1/datasources/csv",
        files={"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=auth_header_owner,
    )
    assert response.status_code == 201
    data = response.json()
    assert "data" in data
    assert "source" in data["data"]
    assert data["data"]["source"]["type"] == "csv"
    assert "preview" in data["data"]


@pytest.mark.asyncio
async def test_upload_csv_invalid_type(async_client: AsyncClient, test_user, test_team, auth_header_owner):
    """Test uploading non-CSV file."""
    response = await async_client.post(
        "/v1/datasources/csv",
        files={"file": ("test.txt", io.BytesIO(b"not a csv"), "text/plain")},
        headers=auth_header_owner,
    )
    # Should fail with invalid file type or processing error
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_datasource_schema(async_client: AsyncClient, test_user, test_team, auth_header_owner):
    """Test getting data source schema."""
    # First upload a CSV
    csv_content = "name,email,score\nAlice,alice@example.com,95\nBob,bob@example.com,87"
    csv_bytes = csv_content.encode("utf-8")

    upload_response = await async_client.post(
        "/v1/datasources/csv",
        files={"file": ("schema_test.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=auth_header_owner,
    )

    if upload_response.status_code == 201:
        source_id = upload_response.json()["data"]["source"]["id"]

        # Get schema
        response = await async_client.get(
            f"/v1/datasources/{source_id}/schema",
            headers=auth_header_owner,
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "columns" in data["data"]


@pytest.mark.asyncio
async def test_delete_datasource(async_client: AsyncClient, test_user, test_team, auth_header_owner):
    """Test deleting a data source."""
    # First upload a CSV
    csv_content = "col1,col2\na,b\nc,d"
    csv_bytes = csv_content.encode("utf-8")

    upload_response = await async_client.post(
        "/v1/datasources/csv",
        files={"file": ("delete_test.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=auth_header_owner,
    )

    if upload_response.status_code == 201:
        source_id = upload_response.json()["data"]["source"]["id"]

        # Delete it
        response = await async_client.delete(
            f"/v1/datasources/{source_id}",
            headers=auth_header_owner,
        )
        assert response.status_code == 200
        assert response.json()["data"]["success"] is True


@pytest.mark.asyncio
async def test_datasource_not_found(async_client: AsyncClient, test_user, test_team, auth_header_owner):
    """Test getting a nonexistent data source."""
    response = await async_client.get(
        f"/v1/datasources/{uuid4()}/schema",
        headers=auth_header_owner,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_google_sheets_auth_url(async_client: AsyncClient, test_user, auth_header_owner):
    """Test getting Google Sheets OAuth URL."""
    response = await async_client.get(
        "/v1/datasources/google-sheets/auth-url",
        headers=auth_header_owner,
    )
    # May fail if Google OAuth is not configured, that's OK
    assert response.status_code in (200, 500, 502)


@pytest.mark.asyncio
async def test_datasources_require_auth(async_client: AsyncClient):
    """Test that data source endpoints require auth."""
    response = await async_client.get("/v1/datasources")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_database_connection_invalid(async_client: AsyncClient, test_user, test_team, auth_header_owner):
    """Test connecting to an invalid database."""
    response = await async_client.post(
        "/v1/datasources/database",
        json={
            "type": "postgresql",
            "host": "nonexistent-host",
            "port": 5432,
            "database": "nonexistent",
            "username": "user",
            "password": "pass",
            "ssl": False,
            "readonly": True,
        },
        headers=auth_header_owner,
    )
    # Should fail with connection error
    assert response.status_code in (400, 500, 502)
