# Rule: Testing

Enforced via `task test:unit`, `task test:coverage`, and `task check:quality`. See
`docs/development/testing.md` for the full strategy.

## Coverage gate

- Overall coverage must be **≥ 97%**, enforced in `task check:quality`.
- Per-context unit suites target **100%** coverage.
- A change that drops coverage below the threshold fails the gate. Do not lower the threshold to
  pass.

## Test pyramid (per context: `users`, `tasks`, `ai`, `shared`)

- **Unit** — the bulk. Domain logic and use cases, with **no DB, AWS, or FastAPI dependency**.
- **Integration** (~10%) — real repositories against a database; includes the RLS isolation test.
- **E2E** (~1%) — full API flow: auth → create → read → update → soft-delete.
- **Architecture** — `import-linter` contracts (run via `task check:architecture`).

Every tier covers happy paths, edge cases, and error scenarios.

## Fakes for ports

- Unit-test use cases against **in-memory fakes** of repository/port interfaces, injected via the
  constructor — never a real DB or SDK.
- The `ai` context uses a **fake `LlmClient`**. **No live Bedrock calls** in the unit or integration
  tiers; live invocation is confined to a gated e2e/smoke suite.

## RLS test needs Postgres

- The **RLS isolation test** must prove a query under one tenant's `app.tenant_id` returns **zero**
  rows from another tenant, even with an unfiltered query.
- RLS is a PostgreSQL feature — this test **cannot** run on SQLite. It requires a real Postgres
  instance via `TEST_DATABASE_URL`.
- Never substitute SQLite or skip this test to make a build green; it validates tenant isolation at
  the same boundary production enforces it.

## When adding code

- Add tests in the same change as the code; defects found in review go back to the Developer, not
  patched in the test.
- A new use case ships with unit tests (happy/edge/error) using fakes; a new repository ships with
  an integration test; tenant-owned tables get RLS coverage.
