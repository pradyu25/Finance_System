"""
Tests for transaction endpoints
==================================
Tests: CRUD operations, filters, validation, role enforcement.

Strategy: We register a user, then directly update their DB role to 'admin'
using the test db_session fixture, then log in to get a valid token.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole
from app.models.transaction import Transaction


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _register_and_login(
    client: AsyncClient,
    db: AsyncSession,
    email: str,
    role: UserRole = UserRole.viewer,
) -> tuple[str, str]:
    """Register, optionally promote to role, login and return (token, user_id)."""
    await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "Test@1234", "full_name": "Test User"},
    )

    # Promote role in DB if needed
    if role != UserRole.viewer:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        user.role = role
        await db.commit()
        await db.refresh(user)

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Test@1234"},
    )
    data = resp.json()["data"]
    return data["access_token"], data["user"]["id"]


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_transaction_requires_auth(client: AsyncClient):
    """Creating a transaction without a token returns 401."""
    resp = await client.post(
        "/api/v1/transactions",
        json={"amount": 100, "type": "income", "category": "Salary", "date": "2024-01-15"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_viewer_cannot_create(client: AsyncClient, db_session: AsyncSession):
    """A viewer should receive 403 when trying to create a transaction."""
    token, _ = await _register_and_login(
        client, db_session, "viewer_create@test.com", UserRole.viewer
    )
    resp = await client.post(
        "/api/v1/transactions",
        json={"amount": 100, "type": "income", "category": "Salary", "date": "2024-01-15"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_and_read_transaction(client: AsyncClient, db_session: AsyncSession):
    """Admin can create; admin can read the transaction back."""
    token, _ = await _register_and_login(
        client, db_session, "admin_create@test.com", UserRole.admin
    )
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post(
        "/api/v1/transactions",
        json={
            "amount": 5000.0,
            "type": "income",
            "category": "Salary",
            "date": "2024-03-01",
            "description": "March salary",
        },
        headers=headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    txn_id = create_resp.json()["data"]["id"]

    get_resp = await client.get(f"/api/v1/transactions/{txn_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["amount"] == 5000.0


@pytest.mark.asyncio
async def test_invalid_amount_rejected(client: AsyncClient, db_session: AsyncSession):
    """Amount ≤ 0 should be rejected by Pydantic validation."""
    token, _ = await _register_and_login(
        client, db_session, "admin_val@test.com", UserRole.admin
    )
    resp = await client.post(
        "/api/v1/transactions",
        json={"amount": -50, "type": "expense", "category": "Food", "date": "2024-03-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_invalid_date_rejected(client: AsyncClient, db_session: AsyncSession):
    """Non-ISO date strings must be rejected."""
    token, _ = await _register_and_login(
        client, db_session, "admin_date@test.com", UserRole.admin
    )
    resp = await client.post(
        "/api/v1/transactions",
        json={"amount": 100, "type": "income", "category": "Other", "date": "15-03-2024"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_transaction(client: AsyncClient, db_session: AsyncSession):
    """Admin can update an existing transaction."""
    token, _ = await _register_and_login(
        client, db_session, "admin_upd@test.com", UserRole.admin
    )
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post(
        "/api/v1/transactions",
        json={"amount": 1000.0, "type": "expense", "category": "Food", "date": "2024-04-01"},
        headers=headers,
    )
    txn_id = create_resp.json()["data"]["id"]

    update_resp = await client.put(
        f"/api/v1/transactions/{txn_id}",
        json={"amount": 1500.0, "description": "Updated"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["amount"] == 1500.0


@pytest.mark.asyncio
async def test_delete_transaction(client: AsyncClient, db_session: AsyncSession):
    """Admin can delete a transaction; subsequent GET returns 404."""
    token, _ = await _register_and_login(
        client, db_session, "admin_del@test.com", UserRole.admin
    )
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post(
        "/api/v1/transactions",
        json={"amount": 200.0, "type": "expense", "category": "Transport", "date": "2024-05-01"},
        headers=headers,
    )
    txn_id = create_resp.json()["data"]["id"]

    delete_resp = await client.delete(f"/api/v1/transactions/{txn_id}", headers=headers)
    assert delete_resp.status_code == 204

    get_resp = await client.get(f"/api/v1/transactions/{txn_id}", headers=headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_list_transactions_pagination(client: AsyncClient, db_session: AsyncSession):
    """Paginated list returns the correct meta fields."""
    token, _ = await _register_and_login(
        client, db_session, "admin_pag@test.com", UserRole.admin
    )
    headers = {"Authorization": f"Bearer {token}"}

    for i in range(5):
        await client.post(
            "/api/v1/transactions",
            json={
                "amount": 100 + i,
                "type": "expense",
                "category": "Food",
                "date": f"2024-0{i+1}-01",
            },
            headers=headers,
        )

    resp = await client.get("/api/v1/transactions?page=1&page_size=2", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "meta" in body
    assert body["meta"]["page"] == 1
    assert body["meta"]["page_size"] == 2
    assert body["meta"]["total"] >= 5
