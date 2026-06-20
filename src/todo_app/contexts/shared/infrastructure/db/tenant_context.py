"""Binds the request's tenant to the DB transaction for RLS enforcement.

Issues ``SET LOCAL app.tenant_id = '<uuid>'`` so PostgreSQL RLS policies can
compare each row's ``tenant_id`` against ``current_setting('app.tenant_id')``.
This is the enforcement seam — app-layer filtering is only defense-in-depth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import text

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


async def bind_tenant(session: AsyncSession, tenant_id: UUID) -> None:
    """Set the tenant for the current transaction (must run inside a tx).

    ``SET LOCAL`` is transaction-scoped, so it resets automatically at commit/
    rollback — no cross-request leakage. Parameter binding guards against
    injection via the bound value.
    """
    await session.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": str(tenant_id)})


def is_postgres(session: AsyncSession) -> bool:
    return session.bind is not None and session.bind.dialect.name == "postgresql"
