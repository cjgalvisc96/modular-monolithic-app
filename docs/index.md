# TODO App

A TODO service built as a **modular monolith** following **Domain-Driven Design**. The
codebase is organized into bounded contexts (`users`, `tasks`, `ai`, `shared`), each owning
a full vertical slice — `domain → application → infrastructure → container.py` — composed at a
single root `ApplicationContainer`.

The system is multi-tenant. Tenant identity flows from an **AWS Cognito** JWT claim, through a
request-scoped session variable, down to **PostgreSQL Row-Level Security** — which is the actual
enforcement boundary, not application-layer filtering. AI features (e.g. task suggestions) live in
their own `ai` context behind an `LlmClient` port, implemented by an **Amazon Bedrock** adapter.

## What to read next

- [Architecture Overview](architecture/overview.md) — the big picture and a context/layer diagram.
- [Bounded Contexts](architecture/bounded-contexts.md) — isolation rules and cross-context ports.
- [Layering](architecture/layering.md) — the dependency direction and how it is enforced.
- [Multi-Tenancy](architecture/multi-tenancy.md) — the Cognito → session var → RLS chain.
- [AI Context](architecture/ai-context.md) — the `LlmClient` port and Bedrock adapter.
- [Decision Records](adr/index.md) — why the system is built the way it is.
- [Development Setup](development/setup.md) — get a local environment running.

## Quick start

The repository uses [`uv`](https://docs.astral.sh/uv/) for Python dependency management and a
[`Taskfile.yml`](https://taskfile.dev/) as the command runner. Everything below is a `task` target.

### 1. Bootstrap the virtual environment

```bash
task create_venv
```

This provisions the `uv`-managed virtual environment and installs the dependency groups
(`prod`, `dev`, `lint`, `test`) declared in `pyproject.toml`.

### 2. Bring up the stack

```bash
task docker:up
```

This starts the application together with **PostgreSQL** and **Redis**. Services use
`depends_on` with healthcheck conditions, so the app only starts once its dependencies report
healthy. Once up:

- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

Tear it down with `task docker:down`. See [Development Setup](development/setup.md) for the full
list of `task` targets.

### 3. Run the quality gates

```bash
task ensure_quality       # ruff, pyright, vulture, coverage gate
task ensure_architecture  # import-linter contracts (layer + context boundaries)
task unit_tests           # the unit tier of the test pyramid
```

## Key constraints

These hold everywhere in the codebase and are enforced by tooling, not convention alone:

- **Dependency direction**: `domain → application → infrastructure`, never reversed. Only a
  context's `container.py` may import across all three layers.
- **Context isolation**: `users`, `tasks`, `ai`, `shared` never import each other's internals;
  cross-context access goes through explicit ports wired at the root `ApplicationContainer`.
- **Presentation purity**: `api/` and `cli/` contain no business logic — they call
  `application/` use cases only.
- **Tenancy boundary**: PostgreSQL RLS, not application `WHERE` filters.
- **IAM**: one least-privilege IRSA role per workload.

The full design is described in the repository's `todo-app-architecture-summary.md`,
`project-structure.md`, and `plan.md`.
