import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test registering a new user successfully."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "strongpassword123",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "id" in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test that registering with an existing email returns 409 Conflict."""
    # Register first user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password12345",
            "full_name": "User One",
        },
    )

    # Register second user with same email
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "differentpass",
            "full_name": "User Two",
        },
    )
    assert response.status_code == 409
    assert response.json()["message"] == "A user with this email address already exists."


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, normal_user: dict):
    """Test standard JSON login with valid credentials."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": normal_user["email"], "password": normal_user["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_incorrect_password(client: AsyncClient, normal_user: dict):
    """Test standard JSON login with incorrect credentials returns 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": normal_user["email"], "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "message" in response.json()


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """Test that fetching profile without a token returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_success(client: AsyncClient, auth_headers: dict, normal_user: dict):
    """Test fetching profile with a valid token returns user data."""
    response = await client.get(
        "/api/v1/auth/me",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == normal_user["email"]
    assert data["full_name"] == normal_user["full_name"]
