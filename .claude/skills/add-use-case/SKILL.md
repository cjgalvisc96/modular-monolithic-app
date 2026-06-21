---
name: add-use-case
description: >-
  Add a command (write) or query (read) use case to an existing bounded context, with input/output
  DTOs, constructor-injected ports, DI wiring, presentation exposure, and tests.
---

# Skill: Add a Use Case

Use this to add behavior to an **existing** context (`users`, `tasks`, `ai`). A use case lives in
`application/`, depends only on `domain/` interfaces, and is exposed through the API and/or CLI.
Follow `.claude/rules/architecture.md` and `.claude/rules/coding-style.md`.

## Decide: command or query?

- **Command** (`application/commands/`) — a **write**: mutates state (e.g. `CreateTaskCommand`,
  `CompleteTaskCommand`, `GenerateTaskSuggestionCommand`).
- **Query** (`application/queries/`) — a **read**: returns data without mutation (e.g.
  `ListTasksQuery`, `GetUserByIdQuery`).

This read/write separation is CQRS-style — keep them in their respective folders.

## Read-side patterns

- **List queries return a `Page[T]`** (`shared/application/page.py`) — `{items, total, limit,
  offset}`; the repository exposes `count(...)` next to `list(...)`, and the router serializes via
  `PageResponse[T].from_page(...)`.
- **GET-by-id routes cache** through `presentation/api/caching.py::cached(...)` (tenant-scoped Redis
  key, TTL), invalidated on the matching writes.
- The API is rate-limited by `presentation/api/middleware/rate_limit.py` (Redis fixed window).

## One-shot ops jobs are not CLI commands

Data seeding and similar init jobs live in `todo_app/scripts/` as standalone entrypoints run as
init containers before the API — they still drive **use cases only**, never repositories/entities.

## Steps

### 1. Define the DTOs

In `application/dto/`, add the input and output DTOs. DTOs are the **application boundary** and are
distinct from API serializers (the HTTP boundary). They should map cleanly to serializers but are
not the same objects.

### 2. Identify the ports it needs

- The use case depends on **domain interfaces** only — e.g. a `TaskRepository` port, or for `ai`,
  the `LlmClient` port.
- If it needs another context's data, depend on a **read-only cross-context port** (e.g. `ai`'s
  task read port, `tasks`' user lookup port). Declare the interface; it is satisfied by wiring at
  the root `ApplicationContainer`. Never import the other context's internals.

### 3. Write the use case

- One class with a single responsibility. Inject its ports via the **constructor**.
- Keep it free of DB, AWS, and FastAPI concerns — it orchestrates domain objects and ports.

```python
class CreateTaskCommand:
    def __init__(self, tasks: TaskRepository) -> None:
        self._tasks = tasks

    async def execute(self, dto: CreateTaskInput) -> CreateTaskOutput:
        ...
```

### 4. Wire it in the context container

In the context's `container.py`, register the use case as a provider, injecting its repositories /
ports. If it uses a cross-context port, ensure that port is passed in from the root
`ApplicationContainer`.

### 5. Expose it (presentation)

- **API**: add a route in `presentation/api/v1/<context>/routers.py`; resolve the use case from the
  container and call it. Map input/output via `serializers.py` (entity-based, **not** DB models).
  No business logic in the router.
- **CLI** (if interactive/admin): add a command in `presentation/cli/commands/<context>.py` that
  invokes the **same** use case class. API and CLI must not duplicate logic. (One-shot jobs go in
  `scripts/` instead — see above.)

### 6. Tests

- **Unit** (`tests/unit/<context>/`) — exercise the use case with **in-memory fakes** of its ports
  (and a fake `LlmClient` for `ai`). Cover happy path, edge cases, and errors.
- **E2E** (if it adds a notable API flow) — extend `tests/e2e/`.
- Maintain coverage **≥ 97%**.

## Verify

```bash
task check:quality        # lint, types, dead code, coverage ≥ 97%
task check:architecture   # boundaries still intact
task test:unit
```
