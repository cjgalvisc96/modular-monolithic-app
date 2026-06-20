# Development Setup

This page gets you from a fresh clone to a running, testable local environment.

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** — Python package and environment manager (the project does
  not use raw `pip`/`venv`).
- **[Task](https://taskfile.dev/)** — the command runner; all workflows are `task` targets defined
  in `Taskfile.yml`.
- **Docker** + Docker Compose — for the local app/Postgres/Redis stack.

`task` checks dependencies before running, lists everything via `task help`, and uses global
variables/aliases defined in `Taskfile.yml`.

## Environment variables

Copy the committed example and fill in values; the real `.env` is gitignored:

```bash
cp .env.example .env
```

The variables include:

```
OWNER=local
DEBUG=true
LOG_LEVEL=DEBUG
DB_*                  # PostgreSQL connection
ATLAS_DIR             # Atlas migrations directory
CORS_*                # API CORS configuration
CACHE_ENABLE=true
CACHE_NAMESPACES      # Redis cache namespaces
REDIS_*               # Redis connection
AWS_REGION
COGNITO_USER_POOL_ID
COGNITO_APP_CLIENT_ID
COGNITO_DOMAIN
BEDROCK_MODEL_ID
```

`core/config.py` loads these into a Pydantic settings object, which feeds the root
`ApplicationContainer`'s configuration provider.

## Bootstrap the environment

```bash
task create_venv
```

Provisions the `uv`-managed virtual environment and installs the dependency groups (`prod`, `dev`,
`lint`, `test`) from `pyproject.toml`.

## Run the stack

```bash
task docker:up      # start app + PostgreSQL + Redis (healthcheck-gated)
task docker:down    # stop the stack
```

Once up: API docs at `http://localhost:8000/docs`, health at `http://localhost:8000/health`.

## Taskfile targets

These are the real targets exposed by `Taskfile.yml`:

| Target | Purpose |
|--------|---------|
| `help` | List all available tasks |
| `create_venv` | Bootstrap the `uv` virtual environment and install dependency groups |
| `linter` | Run static linting (ruff) |
| `ensure_quality` | General quality gate: ruff, pyright, vulture, and the coverage gate |
| `ensure_architecture` | DDD/architecture compliance via import-linter contracts |
| `unit_tests` | Run the unit tier of the test pyramid |
| `coverage` | Run tests and produce the coverage report (gate: ≥ 97%) |
| `remove_cache` | Clean caches |
| `docker:up` | Start the local stack (app + Postgres + Redis) |
| `docker:down` | Stop the local stack |
| `docker:prune` | Remove stack volumes/resources |
| `docker:shell` | Open a shell inside the app container |
| `docker:logs` | Tail the stack logs |

## Typical inner loop

```bash
task ensure_quality        # lint + types + dead-code + coverage gate
task ensure_architecture   # layer + context boundary contracts
task unit_tests            # fast feedback
```

For the full quality gate that mirrors CI, see the `quality-gate` command
(`.claude/commands/quality-gate.md`) in the Claude harness, and the
[Governance](governance.md) page.

## VSCode debugging

`.vscode/launch.json` provides debugger configurations for the FastAPI app and for `pytest`.
