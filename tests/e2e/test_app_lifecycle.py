"""Covers the builder lifespan and the degraded-health (dependency error) path."""

from __future__ import annotations

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from todo_app.core.config import Settings
from todo_app.core.di.container import ApplicationContainer
from todo_app.presentation.api.app import create_app

pytestmark = pytest.mark.asyncio


def _broken_container() -> ApplicationContainer:
    data = Settings().as_provider_dict()
    # Unreachable DB and Redis so both health probes report errors.
    data["database_dsn"] = "postgresql+asyncpg://bad:bad@127.0.0.1:1/none"
    data["cache_enable"] = True
    data["redis_dsn"] = "redis://127.0.0.1:1/0"
    c = ApplicationContainer()
    c.config.from_dict(data)
    return c


async def test_lifespan_runs_and_health_degraded():
    container = _broken_container()
    app = create_app(container=container)
    app.state.container = container
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as client:
            resp = await client.get("/health")
            assert resp.status_code == 503
            body = resp.json()
            assert body["status"] == "degraded"
            assert body["checks"]["database"].startswith("error")
            assert body["checks"]["redis"].startswith("error")
