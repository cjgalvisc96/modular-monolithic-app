"""Bind the request tenant to the DB transaction for RLS (the enforcement seam)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import text

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


async def bind_tenant(session: AsyncSession, tenant_id: UUID) -> None:
    # set_config(..., is_local=true) is transaction-scoped like SET LOCAL but
    # accepts a bound parameter (SET LOCAL does not).
    await session.execute(
        text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": str(tenant_id)}
    )


def is_postgres(session: AsyncSession) -> bool:
    return session.bind is not None and session.bind.dialect.name == "postgresql"
