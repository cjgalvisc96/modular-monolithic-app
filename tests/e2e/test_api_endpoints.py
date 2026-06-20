"""Covers the remaining API surface: reads, updates, auth edge cases, errors."""

from __future__ import annotations

from uuid import uuid4

import pytest

from tests.conftest import dev_headers

pytestmark = pytest.mark.asyncio


async def _make_user(api_client, h, email="u@acme.example.com"):
    r = await api_client.post(
        "/api/v1/users", json={"email": email, "full_name": "U", "role": "admin"}, headers=h
    )
    assert r.status_code == 201, r.text
    return r.json()


async def test_users_read_and_role_change(api_client, tenant_id):
    h = dev_headers(tenant_id)
    user = await _make_user(api_client, h)

    r = await api_client.get("/api/v1/users", headers=h)
    assert r.status_code == 200 and len(r.json()) == 1

    r = await api_client.get(f"/api/v1/users/{user['id']}", headers=h)
    assert r.status_code == 200 and r.json()["email"] == "u@acme.example.com"

    r = await api_client.patch(
        f"/api/v1/users/{user['id']}/role", json={"role": "member"}, headers=h
    )
    assert r.status_code == 200 and r.json()["role"] == "member"


async def test_get_unknown_user_404(api_client, tenant_id):
    h = dev_headers(tenant_id)
    r = await api_client.get(f"/api/v1/users/{uuid4()}", headers=h)
    assert r.status_code == 404


async def test_duplicate_email_409(api_client, tenant_id):
    h = dev_headers(tenant_id)
    await _make_user(api_client, h, "dup@acme.example.com")
    r = await api_client.post(
        "/api/v1/users",
        json={"email": "dup@acme.example.com", "full_name": "Other"},
        headers=h,
    )
    assert r.status_code == 409


async def test_task_read_update_and_filter(api_client, tenant_id):
    h = dev_headers(tenant_id)
    user = await _make_user(api_client, h)
    r = await api_client.post(
        "/api/v1/tasks", json={"owner_id": user["id"], "title": "A"}, headers=h
    )
    task = r.json()

    r = await api_client.get(f"/api/v1/tasks/{task['id']}", headers=h)
    assert r.status_code == 200

    r = await api_client.patch(
        f"/api/v1/tasks/{task['id']}", json={"title": "A2", "description": "d"}, headers=h
    )
    assert r.status_code == 200 and r.json()["title"] == "A2"

    r = await api_client.get(
        f"/api/v1/tasks?owner_id={user['id']}&status_filter=pending", headers=h
    )
    assert r.status_code == 200 and len(r.json()) == 1


async def test_ai_inline_and_background_and_list(api_client, tenant_id):
    h = dev_headers(tenant_id)
    user = await _make_user(api_client, h)

    r = await api_client.post("/api/v1/ai/suggestions", json={"owner_id": user["id"]}, headers=h)
    assert r.status_code == 200 and r.json()["response"]

    r = await api_client.post(
        "/api/v1/ai/suggestions",
        json={"owner_id": user["id"], "background": True},
        headers=h,
    )
    assert r.status_code == 200  # 200 with null body for background dispatch

    r = await api_client.get("/api/v1/ai/suggestions", headers=h)
    assert r.status_code == 200 and len(r.json()) >= 1


async def test_invalid_bearer_token_401(api_client):
    r = await api_client.get("/api/v1/users", headers={"Authorization": "Bearer not.a.jwt"})
    assert r.status_code == 401


async def test_root_endpoint(api_client):
    r = await api_client.get("/")
    assert r.status_code == 200 and "docs" in r.json()


async def test_metrics_endpoint_exposes_prometheus(api_client):
    # Generate some traffic, then scrape /metrics (Prometheus exposition format).
    await api_client.get("/health")
    r = await api_client.get("/metrics")
    assert r.status_code == 200
    assert "# HELP" in r.text
