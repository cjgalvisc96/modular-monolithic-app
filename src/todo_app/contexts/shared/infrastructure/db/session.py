"""Async SQLAlchemy session factory (asyncpg + SQLAlchemy 2.0)."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class Database:
    """Owns the async engine and session factory for the whole app."""

    def __init__(
        self, dsn: str, *, echo: bool = False, pool_size: int = 10, max_overflow: int = 20
    ) -> None:
        # SQLite (tests) does not accept pool sizing args; guard on driver.
        engine_kwargs: dict = {"echo": echo, "future": True}
        if not dsn.startswith("sqlite"):
            engine_kwargs.update(pool_size=pool_size, max_overflow=max_overflow, pool_pre_ping=True)
        self._engine: AsyncEngine = create_async_engine(dsn, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Yield a session wrapped in a transaction (commit on success)."""
        async with self._sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def ping(self) -> bool:
        """Health probe used by /health."""
        from sqlalchemy import text

        async with self._engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True

    async def dispose(self) -> None:
        await self._engine.dispose()
