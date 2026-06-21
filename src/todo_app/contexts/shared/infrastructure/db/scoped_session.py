"""Request-scoped current session holder (contextvar set/reset by the Unit of Work)."""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

_session: ContextVar[AsyncSession | None] = ContextVar("scoped_session", default=None)


def set_current_session(session: AsyncSession | None):
    return _session.set(session)


def reset_current_session(token) -> None:
    _session.reset(token)


def current_session() -> AsyncSession:
    session = _session.get()
    if session is None:
        raise RuntimeError("No active database session; open a UnitOfWork first")
    return session
