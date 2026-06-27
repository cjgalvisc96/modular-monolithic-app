# Rule: Testing

Enforced via `task test:unit`, `task test:coverage`, and `task check:quality`. See
`docs/development/testing.md` for the full strategy.

## Coverage gate

- Overall coverage must be **≥ 97%**, enforced in `task check:quality`.
- Per-context unit suites target **100%** coverage.
- A change that drops coverage below the threshold fails the gate. Do not lower the threshold to
  pass.

## Test pyramid (per context: `users`, `tasks`, `ai`, `shared`)

- **Unit** — the bulk. Domain logic, use cases, **and the presentation layer** (route handlers,
  middleware, serializers, dependencies). The presentation layer is tested by **direct invocation
  with in-memory fakes** — no running FastAPI app, no HTTP client, no DB, no AWS SDK.
- **Integration** (~10%) — real repositories against a database; includes the RLS isolation test.
- **Architecture** — `import-linter` contracts (run via `task check:architecture`).

There is **no separate e2e/HTTP tier**: the API surface is covered at the unit level by calling
handlers directly, which keeps the suite Postgres- and Docker-free in CI. Every tier covers happy
paths, edge cases, and error scenarios.

## Fakes for ports

- Unit-test use cases against **in-memory fakes** of repository/port interfaces, injected via the
  constructor — never a real DB or SDK.
- The `ai` context uses a **fake `LlmClient`**. **No live Bedrock calls** in the unit or integration
  tiers; live invocation is confined to a gated smoke suite.

## RLS test needs Postgres

- The **RLS isolation test** must prove a query under one tenant's `app.tenant_id` returns **zero**
  rows from another tenant, even with an unfiltered query.
- RLS is a PostgreSQL feature — this test **cannot** run on SQLite. It requires a real Postgres
  instance via `TEST_DATABASE_URL`, and **self-skips** (never silently passes) when one is absent.
- Never substitute SQLite to make this test pass; it validates tenant isolation at the same boundary
  production enforces it. The default CI job runs Postgres-free, so exercise it against a real
  Postgres locally (`TEST_DATABASE_URL=… task test:integration`) or in a dedicated Postgres-backed
  run before trusting tenant isolation.

## When adding code

- Add tests in the same change as the code; defects found in review go back to the Developer, not
  patched in the test.
- A new use case ships with unit tests (happy/edge/error) using fakes; a new repository ships with
  an integration test; tenant-owned tables get RLS coverage.
