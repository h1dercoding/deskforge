"""Tests for authentication endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(async_client: AsyncClient):
    """Test user registration."""
    response = await async_client.post(
        "/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "NewUser123!",
            "name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "data" in data
    assert "user" in data["data"]
    assert "tokens" in data["data"]
    assert data["data"]["user"]["email"] == "newuser@example.com"
    assert data["data"]["user"]["name"] == "New User"
    assert "access_token" in data["data"]["tokens"]
    assert "refresh_token" in data["data"]["tokens"]
    # Verify password requirements are included in response
    assert "password_requirements" in data["data"]
    reqs = data["data"]["password_requirements"]
    assert "min_length" in reqs
    assert "description" in reqs


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient, test_user):
    """Test registration with existing email."""
    response = await async_client.post(
        "/v1/auth/register",
        json={
            "email": test_user.email,
            "password": "Duplicate123!",
            "name": "Duplicate User",
        },
    )
    assert response.status_code == 409
    data = response.json()
    assert "error" in data
    assert data["error"]["type"] == "CONFLICT"


@pytest.mark.asyncio
async def test_register_weak_password(async_client: AsyncClient):
    """Test registration with weak password."""
    response = await async_client.post(
        "/v1/auth/register",
        json={
            "email": "weak@example.com",
            "password": "weak",
            "name": "Weak User",
        },
    )
    assert response.status_code == 422  # Pydantic validation


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, test_user):
    """Test successful login."""
    response = await async_client.post(
        "/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "TestPass123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "user" in data["data"]
    assert "tokens" in data["data"]
    assert data["data"]["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient, test_user):
    """Test login with wrong password."""
    response = await async_client.post(
        "/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "WrongPassword123!",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient):
    """Test login with nonexistent email."""
    response = await async_client.post(
        "/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "Whatever123!",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(async_client: AsyncClient, test_user, auth_header_owner):
    """Test getting current user profile."""
    response = await async_client.get(
        "/v1/auth/me",
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["user"]["email"] == "test@example.com"
    assert data["data"]["user"]["name"] == "Test User"


@pytest.mark.asyncio
async def test_get_me_no_auth(async_client: AsyncClient):
    """Test getting profile without auth."""
    response = await async_client.get("/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_me(async_client: AsyncClient, test_user, auth_header_owner):
    """Test updating user profile."""
    response = await async_client.patch(
        "/v1/auth/me",
        json={"name": "Updated Name"},
        headers=auth_header_owner,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["user"]["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_refresh_token(async_client: AsyncClient, test_user):
    """Test JWT token refresh."""
    # First login to get tokens
    login_response = await async_client.post(
        "/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "TestPass123!",
        },
    )
    assert login_response.status_code == 200
    tokens = login_response.json()["data"]["tokens"]

    # Use refresh token
    response = await async_client.post(
        "/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "access_token" in data["data"]


@pytest.mark.asyncio
async def test_forgot_password(async_client: AsyncClient, test_user):
    """Test forgot password endpoint."""
    response = await async_client.post(
        "/v1/auth/forgot-password",
        json={"email": "test@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["sent"] is True


@pytest.mark.asyncio
async def test_verify_email(async_client: AsyncClient, test_user):
    """Test email verification endpoint."""
    response = await async_client.post(
        "/v1/auth/verify-email",
        json={"token": "invalid-token-for-testing"},
    )
    # May fail with invalid token, that's OK - we're testing the endpoint exists
    assert response.status_code in (200, 400, 401)
