"""Full API flow: auth → create user → create task → complete → AI suggestion.

Uses the DEBUG dev-auth header bypass (no Cognito) and the SQLite-backed test
container. RLS is not exercised here (SQLite); see the RLS isolation test.
"""

import pytest

from tests.conftest import dev_headers

pytestmark = pytest.mark.asyncio


async def test_health_ok(api_client):
    resp = await api_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["checks"]["database"] == "ok"


async def test_unauthenticated_rejected(api_client):
    resp = await api_client.get("/api/v1/users")
    assert resp.status_code == 401


async def test_full_crud_flow(api_client, tenant_id):
    h = dev_headers(tenant_id)

    # create a user (admin-gated)
    r = await api_client.post(
        "/api/v1/users",
        json={"email": "owner@acme.example.com", "full_name": "Owner", "role": "admin"},
        headers=h,
    )
    assert r.status_code == 201, r.text
    user = r.json()
    assert user["tenant_id"] == str(tenant_id)

    # create a task owned by that user
    r = await api_client.post(
        "/api/v1/tasks",
        json={"owner_id": user["id"], "title": "Ship it"},
        headers=h,
    )
    assert r.status_code == 201, r.text
    task = r.json()
    assert task["status"] == "pending"

    # complete the task
    r = await api_client.post(f"/api/v1/tasks/{task['id']}/complete", headers=h)
    assert r.status_code == 200
    assert r.json()["status"] == "completed"

    # list tasks
    r = await api_client.get("/api/v1/tasks", headers=h)
    assert r.status_code == 200
    assert len(r.json()["items"]) == 1

    # AI suggestion (stub LLM in debug)
    r = await api_client.post(
        "/api/v1/ai/suggestions",
        json={"owner_id": user["id"]},
        headers=h,
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "completed"
    assert r.json()["response"]


async def test_non_admin_cannot_create_user(api_client, tenant_id):
    h = dev_headers(tenant_id, roles="member")
    r = await api_client.post(
        "/api/v1/users",
        json={"email": "x@acme.example.com", "full_name": "X"},
        headers=h,
    )
    assert r.status_code == 403


async def test_create_task_unknown_owner_422(api_client, tenant_id):
    from uuid import uuid4

    h = dev_headers(tenant_id)
    r = await api_client.post(
        "/api/v1/tasks",
        json={"owner_id": str(uuid4()), "title": "x"},
        headers=h,
    )
    assert r.status_code == 422
