# TODO App — Modular Monolith (DDD)

A multi-tenant TODO service built as a **modular monolith** with **Domain-Driven Design**:
bounded contexts (`users`, `tasks`, `ai`, `shared`), strict `domain → application → infrastructure`
layering, per-context DI containers, AWS Cognito auth, Amazon Bedrock for AI suggestions, and
PostgreSQL Row-Level Security for tenant isolation.

See [`plan.md`](plan.md), [`project-structure.md`](project-structure.md), and
[`todo-app-architecture-summary.md`](todo-app-architecture-summary.md) for the full design.

## Quick start

```bash
task create_venv      # bootstrap venv + deps (uv), copy .env
task docker:up        # app + postgres + redis, waits for healthy
open http://localhost:8000/docs
```

`task help` lists every command.

## Layout

| Path | Purpose |
|---|---|
| `src/todo_app/contexts/` | Bounded contexts, each a vertical `domain/application/infrastructure/container.py` slice |
| `src/todo_app/core/` | Config, DI root (`ApplicationContainer`), logging, telemetry |
| `src/todo_app/presentation/` | `api/` (FastAPI) and `cli/` (Typer) — call application use cases only |
| `migrations/` | Atlas migrations + RLS policies |
| `tests/` | unit / integration / e2e / architecture |
| `infra/` | Helm (`k8s/`), Terraform + Terragrunt, infra tests |
| `observability/` | OTel collector config + Grafana dashboards |
| `docs/` | MkDocs site |

## Architecture guarantees (enforced)

- **Layer direction** and **context isolation** — `task ensure_architecture` (import-linter).
- **Tenant isolation** — JWT `tenant_id` claim → `SET LOCAL app.tenant_id` → PostgreSQL RLS.
- **Quality gate** — `task ensure_quality` (ruff, pyright, vulture, ≥97% coverage).

## Tooling

uv · FastAPI · Typer · SQLAlchemy (asyncpg) · Redis · dependency-injector · Atlas · pytest ·
ruff · pyright · import-linter · Helm · Terraform/Terragrunt · OpenTelemetry · MkDocs.
