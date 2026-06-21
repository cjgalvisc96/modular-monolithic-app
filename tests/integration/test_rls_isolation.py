"""PostgreSQL Row-Level Security isolation test (the tenancy enforcement boundary).

Proves that a query running under one tenant's ``app.tenant_id`` cannot see
another tenant's rows — *even with a completely unfiltered* ``SELECT *``. This is
the guarantee the whole multi-tenancy design rests on: a repository bug cannot
leak cross-tenant data because the database itself rejects the rows.

Requires a real PostgreSQL (RLS is a no-op on SQLite), so it is skipped unless
``TEST_DATABASE_URL`` points at one. CI / local: start one with
``docker run -e POSTGRES_USER=todo -e POSTGRES_PASSWORD=todo -e POSTGRES_DB=todo \\
  -p 5433:5432 postgres:16-alpine`` and set
``TEST_DATABASE_URL=postgresql://todo:todo@localhost:5433/todo``.
"""

import os
from uuid import uuid4

import pytest

asyncpg = pytest.importorskip("asyncpg")

DSN = os.environ.get("TEST_DATABASE_URL")

pytestmark = [
    pytest.mark.skipif(not DSN, reason="TEST_DATABASE_URL not set (needs PostgreSQL)"),
]

SCHEMA = """
DROP TABLE IF EXISTS tasks CASCADE;
CREATE TABLE tasks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL,
    owner_id uuid NOT NULL,
    title varchar(300) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON tasks;
CREATE POLICY tenant_isolation ON tasks
    USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
"""


async def _connect():
    # asyncpg uses the bare postgresql:// scheme (no +driver suffix).
    dsn = DSN.replace("postgresql+asyncpg://", "postgresql://")
    return await asyncpg.connect(dsn)


async def _setup(conn) -> None:
    await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    await conn.execute(SCHEMA)
    # A non-superuser role so RLS is actually enforced (superusers bypass it).
    await conn.execute(
        """
        DROP ROLE IF EXISTS rls_app;
        CREATE ROLE rls_app NOLOGIN;
        GRANT SELECT, INSERT ON tasks TO rls_app;
        """
    )


async def _insert_task(conn, tenant_id, title) -> None:
    async with conn.transaction():
        await conn.execute("SET LOCAL ROLE rls_app")
        await conn.execute("SELECT set_config('app.tenant_id', $1, true)", str(tenant_id))
        await conn.execute(
            "INSERT INTO tasks (tenant_id, owner_id, title) VALUES ($1, $2, $3)",
            tenant_id,
            uuid4(),
            title,
        )


async def _rows_visible_to(conn, tenant_id) -> list:
    async with conn.transaction():
        await conn.execute("SET LOCAL ROLE rls_app")
        await conn.execute("SELECT set_config('app.tenant_id', $1, true)", str(tenant_id))
        # Deliberately UNFILTERED — RLS, not the WHERE clause, must isolate.
        return await conn.fetch("SELECT tenant_id, title FROM tasks")


@pytest.mark.asyncio
async def test_rls_blocks_cross_tenant_reads():
    tenant_a, tenant_b = uuid4(), uuid4()
    conn = await _connect()
    try:
        await _setup(conn)
        await _insert_task(conn, tenant_a, "A-secret")
        await _insert_task(conn, tenant_b, "B-secret")

        a_rows = await _rows_visible_to(conn, tenant_a)
        b_rows = await _rows_visible_to(conn, tenant_b)

        assert {r["title"] for r in a_rows} == {"A-secret"}
        assert {r["title"] for r in b_rows} == {"B-secret"}
        # Tenant A's unfiltered query saw exactly one row — never tenant B's.
        assert all(r["tenant_id"] == tenant_a for r in a_rows)
        assert all(r["tenant_id"] == tenant_b for r in b_rows)
    finally:
        await conn.execute("DROP TABLE IF EXISTS tasks CASCADE; DROP ROLE IF EXISTS rls_app;")
        await conn.close()


@pytest.mark.asyncio
async def test_rls_write_check_rejects_foreign_tenant():
    """WITH CHECK must forbid inserting a row for a different tenant than the session."""
    tenant_a, tenant_b = uuid4(), uuid4()
    conn = await _connect()
    try:
        await _setup(conn)
        with pytest.raises(asyncpg.PostgresError):
            async with conn.transaction():
                await conn.execute("SET LOCAL ROLE rls_app")
                await conn.execute("SELECT set_config('app.tenant_id', $1, true)", str(tenant_a))
                # Trying to write a row belonging to tenant B → rejected by WITH CHECK.
                await conn.execute(
                    "INSERT INTO tasks (tenant_id, owner_id, title) VALUES ($1, $2, $3)",
                    tenant_b,
                    uuid4(),
                    "smuggled",
                )
    finally:
        await conn.execute("DROP TABLE IF EXISTS tasks CASCADE; DROP ROLE IF EXISTS rls_app;")
        await conn.close()
