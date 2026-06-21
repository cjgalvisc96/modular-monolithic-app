# Testing

The test suite is a **test pyramid**, applied per bounded context (`users`, `tasks`, `ai`,
`shared`). Every tier covers happy paths, edge cases, and error scenarios. It is run with `pytest`,
using `aiosqlite` where a lightweight in-process database suffices and real PostgreSQL where RLS
must be exercised.

```mermaid
flowchart TB
    E2E["e2e — ~1%<br/>full API flow: auth → create → read → update → soft-delete"]
    INT["integration — ~10%<br/>real repositories + DB; RLS isolation test"]
    UNIT["unit — bulk<br/>domain + use cases with in-memory fakes"]
    ARCH["architecture — import-linter<br/>layer + context boundary contracts"]
    UNIT --> INT --> E2E
    ARCH -.enforces boundaries.-> UNIT
```

## The tiers

- **Unit** (`tests/unit/{users,tasks,ai,shared}/`) — the bulk of the suite, with a **100% coverage
  target** per context. Domain logic and use cases are tested in isolation. Use cases run against
  **in-memory fakes** of repository/port interfaces — no DB, no AWS, no FastAPI. The `ai` context
  uses a **fake `LlmClient`**; there are **no live Bedrock calls** in this tier.
- **Integration** (`tests/integration/{users,tasks,ai}/`) — ~10% of the suite. Repository and
  DB-level tests using real repository implementations. Includes the **RLS isolation test**
  (below).
- **End-to-end** (`tests/e2e/`) — ~1% of the suite. Full API flows: authenticate, create, read,
  update, soft-delete, across contexts.
- **Architecture** (`tests/architecture/`) — `import-linter`-backed tests asserting layer
  boundaries and context isolation, including the rule that only `container.py` may import across
  all three layers of a context. See [Governance](governance.md).

## The RLS isolation test (needs real Postgres)

The cornerstone integration test asserts that a query run under **one** tenant's session variable
returns **zero** rows belonging to another tenant — even with an **unfiltered** query. This proves
that tenancy is enforced by the database (RLS), not by application `WHERE` clauses (see
[Multi-Tenancy](../architecture/multi-tenancy.md)).

Because Row-Level Security is a PostgreSQL feature, this test **cannot** run against SQLite. It
requires a real Postgres instance, configured via:

```
TEST_DATABASE_URL=postgresql+asyncpg://<user>:<pass>@<host>:<port>/<db>
```

With `task docker:up` running, the floci Aurora datastore is exposed on the host, so point
`TEST_DATABASE_URL` at `postgresql+asyncpg://todo:todopassword@localhost:5432/todo`.

## Coverage gate

Overall coverage must be **≥ 97%**, enforced in `task check:quality` (and reported by
`task test:coverage`). Pull requests that drop coverage below the threshold fail the gate.

## Running tests

```bash
task test:unit            # unit tier (fast)
task test:coverage              # full run + coverage report (gate ≥ 97%)
task check:architecture   # architecture/import-linter contracts
```
