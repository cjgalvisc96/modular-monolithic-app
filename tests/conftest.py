from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from tests.support.containers import build_sqlite_container
from todo_app.presentation.api.app import create_app

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest_asyncio.fixture
async def container(tmp_path) -> AsyncIterator:
    db_file = tmp_path / "test.db"
    c = await build_sqlite_container(str(db_file))
    yield c
    await c.shared.database().dispose()


@pytest_asyncio.fixture
async def api_client(container) -> AsyncIterator[AsyncClient]:
    app = create_app(container=container)
    app.state.container = container
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def dev_headers(tenant_id, roles: str = "admin,member") -> dict[str, str]:
    """Headers for the DEBUG dev-auth bypass (no Cognito needed in tests)."""
    return {"X-Dev-Tenant": str(tenant_id), "X-Dev-Roles": roles}
