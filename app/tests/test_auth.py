"""
Tests for authentication endpoints
=====================================
Tests: registration, duplicate email, login success, login failure.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_success(client: AsyncClient):
    """A new user can register successfully."""
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "alice@test.com", "password": "Secret@123", "full_name": "Alice"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"]["email"] == "alice@test.com"
    assert body["data"]["role"] == "viewer"


@pytest.mark.asyncio
async def test_signup_duplicate_email(client: AsyncClient):
    """Registering with an existing email returns 409."""
    payload = {"email": "bob@test.com", "password": "Secret@123", "full_name": "Bob"}
    await client.post("/api/v1/auth/signup", json=payload)
    resp = await client.post("/api/v1/auth/signup", json=payload)
    assert resp.status_code == 409
    assert resp.json()["status"] == "error"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """A registered user can log in and receive a JWT."""
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "carol@test.com", "password": "Pass@word1", "full_name": "Carol"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "carol@test.com", "password": "Pass@word1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "access_token" in body["data"]


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Wrong password returns 401."""
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "dave@test.com", "password": "Pass@word1", "full_name": "Dave"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "dave@test.com", "password": "WrongPass"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient):
    """Unknown email returns 401."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@test.com", "password": "anything"},
    )
    assert resp.status_code == 401
