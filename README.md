# TODO App — Modular Monolith (DDD)

A multi-tenant TODO service built as a **modular monolith** with **Domain-Driven Design**:
bounded contexts (`users`, `tasks`, `ai`, `shared`), strict `domain → application → infrastructure`
layering, per-context DI containers, AWS Cognito auth, Amazon Bedrock for AI suggestions, and
PostgreSQL Row-Level Security for tenant isolation. Runs on **Python 3.14**.

## 📖 Documentation

The full project documentation is a **MkDocs site** — this is the place to read everything
(architecture, ADRs, development, operations, GitOps):

```bash
task docs:serve     # → http://127.0.0.1:8001
```

`task docs:build` renders the static site. The high-level planning docs live at the repo root
([`enterpise-plan.md`](enterpise-plan.md), [`copier-plan.md`](copier-plan.md)).

## Quick start

There are **two ways to run it** — see the **[Launch](docs/launch.md)** page (also in the docs site)
for the simple step-by-step. The fast one:

```bash
task env:create      # uv venv (Python 3.14) + deps + .env
task docker:up        # ordered bring-up: floci → terraform → atlas → seed → API
open http://localhost:8000/docs     # Swagger (live API reference)
```

A single `task docker:up` gives a fully provisioned, migrated, seeded, host-reachable stack.
`task help` lists every command. To run it the production way (built by a pipeline, deployed by Argo
CD on the local-gitops lab), follow **Option B** on the Launch page.

### What runs locally (AWS, simulated by floci)

| Production | Local (floci) | On host |
|---|---|---|
| Aurora (RDS Postgres) | `floci-rds-todo-aurora` | `localhost:5432` |
| ElastiCache (Redis) | `floci-valkey-todo-redis` (Valkey) | `localhost:6379` |
| ECR + SSM | floci ECR / SSM | via the `floci` AWS profile |

## Layout

| Path | Purpose |
|---|---|
| `src/todo_app/contexts/` | Bounded contexts, each a vertical `domain/application/infrastructure/container.py` slice |
| `src/todo_app/core/` | Config, DI root (`ApplicationContainer`), logging, telemetry |
| `src/todo_app/presentation/` | `api/` (FastAPI) and `cli/` (Typer) — call application use cases only |
| `src/todo_app/scripts/` | One-shot ops entry points (e.g. the demo-data seeder) |
| `migrations/` | Atlas migrations + RLS policies |
| `tests/` | unit / integration / architecture |
| `infra/` | Helm (`k8s/helm`), GitOps (`k8s/gitops`), local datastores (`k8s/dependencies`), Terraform + Terragrunt |
| `observability/` | OTel collector config + Grafana dashboards |
| `docs/` | MkDocs site |

## Entry points

Installed by `uv` as console scripts (used by the container and locally):

| Script | Purpose |
|---|---|
| `todo-api` | Serve the FastAPI app (uvicorn); `API_RELOAD=1` enables hot-reload |
| `todo-seed` | One-shot demo-data seeder (runs as the `seed` init container) |
| `todo-cli` | Admin/operational CLI (Typer) |

## Architecture guarantees (enforced)

- **Layer direction** and **context isolation** — `task check:architecture` (import-linter).
- **Tenant isolation** — Cognito `tenant_id` claim → `set_config('app.tenant_id', …, true)` →
  PostgreSQL RLS.
- **Quality gate** — `task check:quality` (ruff, pyright, vulture, ≥97% coverage).

## Deployment

Pull-based via **Argo CD** on the [local-gitops](https://github.com/cjgalvisc96/local-gitops)
platform: the app ships its own Helm chart, datastores, and GitOps registration, while the platform
stays generic. See [`infra/k8s/gitops/`](infra/k8s/gitops) and the **GitOps Deployment** page in the
docs site.

## Tooling

uv · Python 3.14 · FastAPI · Typer · SQLAlchemy (asyncpg) · Redis · dependency-injector · Atlas ·
pytest · ruff · pyright · import-linter · Helm · Argo CD · Terraform/Terragrunt · floci ·
OpenTelemetry · MkDocs.
