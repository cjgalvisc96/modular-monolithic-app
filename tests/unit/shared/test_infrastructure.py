"""Unit tests for shared infrastructure primitives (with fakes — no real I/O)."""

from __future__ import annotations

from contextlib import asynccontextmanager
from uuid import uuid4

import pytest

from todo_app.contexts.shared.application.request_context import (
    RequestContext,
    bind_context,
    current_context,
    require_context,
)
from todo_app.contexts.shared.domain.events.base import DomainEvent
from todo_app.contexts.shared.domain.value_objects.identifier import EntityId
from todo_app.contexts.shared.infrastructure.cache.redis_cache import RedisCache
from todo_app.contexts.shared.infrastructure.db.scoped_session import current_session
from todo_app.contexts.shared.infrastructure.db.session import Database
from todo_app.contexts.shared.infrastructure.db.tenant_context import bind_tenant, is_postgres
from todo_app.contexts.shared.infrastructure.db.unit_of_work import UnitOfWork
from todo_app.contexts.shared.infrastructure.messaging.in_memory_bus import (
    InMemoryEventPublisher,
)


# --- request context ---------------------------------------------------------
async def test_request_context_bind_and_require():
    assert current_context() is None
    with pytest.raises(RuntimeError):
        require_context()
    ctx = RequestContext(tenant_id=uuid4(), roles=frozenset({"admin"}))
    with bind_context(ctx):
        assert require_context() is ctx
        assert ctx.has_role("admin")
    assert current_context() is None


def test_entity_id_str():
    eid = EntityId.generate()
    assert str(eid) == str(eid.value)


# --- scoped session ----------------------------------------------------------
async def test_current_session_requires_active_session():
    with pytest.raises(RuntimeError):
        current_session()


# --- redis cache (fake redis) ------------------------------------------------
class _FakeRedis:
    def __init__(self):
        self.store: dict[str, bytes] = {}

    async def get(self, k):
        return self.store.get(k)

    async def set(self, k, v, ex=None):
        self.store[k] = v.encode() if isinstance(v, str) else v

    async def delete(self, k):
        self.store.pop(k, None)

    async def ping(self):
        return True

    async def aclose(self):
        return None


async def test_redis_cache_roundtrip_and_namespace_guard():
    cache = RedisCache(_FakeRedis(), enabled=True, namespaces=("users",))
    assert await cache.get("users", "k") is None
    await cache.set("users", "k", "v")
    assert await cache.get("users", "k") == "v"
    await cache.invalidate("users", "k")
    assert await cache.get("users", "k") is None
    assert await cache.ping() is True
    with pytest.raises(ValueError):
        await cache.set("unknown", "k", "v")
    await cache.close()


async def test_redis_cache_disabled_is_noop():
    cache = RedisCache(_FakeRedis(), enabled=False)
    await cache.set("x", "k", "v")
    assert await cache.get("x", "k") is None
    await cache.invalidate("x", "k")
    assert await cache.ping() is True


# --- event bus ---------------------------------------------------------------
async def test_event_bus_dispatches_to_subscribers():
    bus = InMemoryEventPublisher()
    seen = []

    async def handler(event):
        seen.append(event)

    bus.subscribe("DomainEvent", handler)
    await bus.publish_all([DomainEvent(), DomainEvent()])
    assert len(seen) == 2


# --- database (real sqlite) --------------------------------------------------
async def test_database_ping_session_and_rollback():
    db = Database("sqlite+aiosqlite:///:memory:")
    assert await db.ping() is True
    with pytest.raises(ValueError):
        async with db.session():
            raise ValueError("boom")  # forces rollback path
    await db.dispose()


# --- tenant context (fake session) -------------------------------------------
class _FakeDialect:
    name = "postgresql"


class _FakeBind:
    dialect = _FakeDialect()


class _FakeSession:
    def __init__(self):
        self.bind = _FakeBind()
        self.executed: list = []

    async def execute(self, stmt, params=None):
        self.executed.append((str(stmt), params))


async def test_bind_tenant_issues_set_local():
    session = _FakeSession()
    tid = uuid4()
    await bind_tenant(session, tid)
    assert session.executed and session.executed[0][1] == {"tid": str(tid)}
    assert is_postgres(session) is True


# --- unit of work postgres branch (fakes) ------------------------------------
class _FakeDatabase:
    def __init__(self, session):
        self._session = session

    @asynccontextmanager
    async def session(self):
        yield self._session


async def test_unit_of_work_binds_tenant_on_postgres():
    from todo_app.contexts.shared.infrastructure.db.scoped_session import current_session

    session = _FakeSession()
    uow = UnitOfWork(_FakeDatabase(session))
    tid = uuid4()
    async with uow.begin(tid):
        assert current_session() is session
    # SET LOCAL app.tenant_id was issued for the postgres session
    assert any(params == {"tid": str(tid)} for _, params in session.executed)
