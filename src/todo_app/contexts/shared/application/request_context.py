"""Request-scoped identity/tenant context.

Populated by the API tenant-binding middleware (or the CLI) from the verified
JWT, read by the DB tenant_context to issue `SET LOCAL app.tenant_id`. Kept in a
``contextvar`` so it is correct under async concurrency without threading it
through every call signature.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID


@dataclass(frozen=True, slots=True)
class RequestContext:
    tenant_id: UUID
    user_id: UUID | None = None
    roles: frozenset[str] = field(default_factory=frozenset)

    def has_role(self, role: str) -> bool:
        return role in self.roles


_current: ContextVar[RequestContext | None] = ContextVar("request_context", default=None)


def current_context() -> RequestContext | None:
    return _current.get()


def require_context() -> RequestContext:
    ctx = _current.get()
    if ctx is None:
        raise RuntimeError("No RequestContext bound; tenant cannot be resolved")
    return ctx


@contextmanager
def bind_context(ctx: RequestContext):
    token = _current.set(ctx)
    try:
        yield ctx
    finally:
        _current.reset(token)
