"""Build an ApplicationContainer backed by a throwaway SQLite database.

Used by integration + e2e tests so repositories, the Unit of Work, and the API
run against a real (if simpler) database. RLS is NOT exercised here — the
dedicated RLS isolation test runs against PostgreSQL.
"""

from __future__ import annotations

from todo_app.contexts.shared.infrastructure.db.registry import metadata
from todo_app.core.config import Settings
from todo_app.core.di.container import ApplicationContainer


async def build_sqlite_container(db_path: str) -> ApplicationContainer:
    settings = Settings(debug=True)
    data = settings.as_provider_dict()
    data["database_dsn"] = f"sqlite+aiosqlite:///{db_path}"
    data["debug"] = True
    data["db_echo"] = False
    data["cache_enable"] = False  # no Redis in the test harness; health stays green

    container = ApplicationContainer()
    container.config.from_dict(data)

    engine = container.shared.database().engine
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    return container
