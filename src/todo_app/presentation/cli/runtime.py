"""CLI runtime helpers — share the same ApplicationContainer and use cases as the API."""

import asyncio
from typing import TYPE_CHECKING

from todo_app.contexts.shared.application.request_context import (
    RequestContext,
    bind_context,
)
from todo_app.core.config import get_settings
from todo_app.core.di.container import ApplicationContainer, build_container

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from uuid import UUID

_container: ApplicationContainer | None = None


def container() -> ApplicationContainer:
    global _container
    if _container is None:
        _container = build_container(get_settings())
    return _container


def run_in_context(tenant_id: UUID, coro_factory: Callable[[], Awaitable]):
    """Run a use case inside a bound RequestContext + tenant-scoped Unit of Work."""
    ctx = RequestContext(tenant_id=tenant_id, user_id=None, roles=frozenset({"admin"}))
    uow = container().shared.unit_of_work()

    async def _run():
        with bind_context(ctx):
            async with uow.begin(tenant_id):
                return await coro_factory()

    return asyncio.run(_run())
