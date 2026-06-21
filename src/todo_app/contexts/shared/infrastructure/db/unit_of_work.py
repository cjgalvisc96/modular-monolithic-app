"""Unit of Work — one transaction per operation, tenant-bound for RLS."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from todo_app.contexts.shared.application.request_context import current_context
from todo_app.contexts.shared.infrastructure.db.scoped_session import (
    reset_current_session,
    set_current_session,
)
from todo_app.contexts.shared.infrastructure.db.tenant_context import bind_tenant, is_postgres

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from uuid import UUID

    from todo_app.contexts.shared.infrastructure.db.session import Database


class UnitOfWork:
    def __init__(self, database: Database) -> None:
        self._database = database

    @asynccontextmanager
    async def begin(self, tenant_id: UUID | None = None) -> AsyncIterator[None]:
        ctx = current_context()
        effective_tenant = tenant_id or (ctx.tenant_id if ctx else None)
        async with self._database.session() as session:
            if effective_tenant is not None and is_postgres(session):
                await bind_tenant(session, effective_tenant)
            token = set_current_session(session)
            try:
                yield
            finally:
                reset_current_session(token)
