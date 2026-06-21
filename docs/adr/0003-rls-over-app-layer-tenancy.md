# ADR-0003: PostgreSQL RLS over application-layer tenant filtering

## Status

Accepted

## Context

The application is multi-tenant on a shared PostgreSQL schema: every tenant-owned table has a
`tenant_id` column. We must guarantee that one tenant can never read or write another tenant's
rows.

The conventional approach is application-layer filtering: every repository query appends
`WHERE tenant_id = :current_tenant`. This works only as long as **every** query, on **every** code
path, forever, remembers the filter. A single missing `WHERE`, a raw SQL query, a join that drops
the scope, or a new endpoint written under deadline pressure becomes a cross-tenant data leak — the
most severe class of bug a multi-tenant system can have. Correctness depends on perfect developer
discipline across the entire codebase's lifetime.

## Decision

Make **PostgreSQL Row-Level Security (RLS)** the tenancy enforcement boundary. Every tenant-owned
table has an RLS policy (`migrations/policies/*.sql`, applied via Atlas) of the form:

```sql
CREATE POLICY tenant_isolation ON tasks
  USING (tenant_id = current_setting('app.tenant_id')::uuid);
```

The current tenant is bound per transaction via `set_config('app.tenant_id', '<value>', true)` (the
parameterized, transaction-local form) in
`shared/infrastructure/db/tenant_context.py`, sourced from the verified Cognito `tenant_id` claim
through the tenant-binding middleware.

Application-layer filtering by `tenant_id`, where present, is treated as **defense-in-depth**, not
the source of truth.

## Consequences

- **Positive — leak-proof by construction.** A repository bug cannot leak cross-tenant data; the
  database itself refuses rows that do not match the session's `tenant_id`, regardless of what the
  query filters on.
- **Positive — correctness is centralized.** Tenant isolation lives in a handful of policy files
  and one `set_config` call, not scattered across every query.
- **Negative — every transaction must set the session var.** Any DB access that forgets to set
  `app.tenant_id` will see no rows (fail closed). This is enforced by the tenant-binding path and
  must be respected by CLI/background code paths too.
- **Negative — testing requires real Postgres.** RLS is a PostgreSQL feature and cannot be
  exercised against SQLite; the RLS isolation test needs a real Postgres instance
  (`TEST_DATABASE_URL`). See [Testing](../development/testing.md).
- **Negative — transaction-scoped binding and connection pooling.** Because the setting is transaction-scoped, the
  tenant variable must be set inside the transaction that runs the query so it cannot leak across
  pooled connections.
