# Development Setup

From a fresh clone to a running, testable local environment.

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** — Python toolchain manager. The project targets **Python
  3.14** (`requires-python >= 3.14`); uv provisions the interpreter, so you don't install Python
  yourself.
- **[Task](https://taskfile.dev/)** — the command runner; every workflow is a `task` target in
  `Taskfile.yml` (`task help` lists them).
- **Docker** + Compose — runs the local stack.
- **Terraform** — provisions the local AWS resources inside floci (see below).
- **AWS CLI** *(optional)* — only for inspecting floci directly; `task` creates the local `floci`
  profile for you.

## Local stack = AWS, simulated by floci

The local environment mirrors the cloud topology using **floci** (a local AWS emulator) instead of
plain containers:

| Production | Local (floci) | Reachable on host |
|---|---|---|
| Aurora (RDS Postgres) | `floci-rds-todo-aurora` | `localhost:5432` |
| ElastiCache (Redis) | `floci-valkey-todo-redis` (Valkey) | `localhost:6379` |
| ECR + SSM | floci ECR / SSM | via the `floci` AWS profile |

`task docker:up` runs an ordered bring-up that mirrors the real pipeline:

1. **floci** starts (the local AWS).
2. **Terraform** (`ENV=local`, `infra/terraform/local`) provisions ECR, SSM, Aurora and
   ElastiCache inside floci.
3. The **`atlas`** init container applies the schema migrations to Aurora.
4. The **`seed`** init container loads demo data (`todo_app/scripts/seed.py`) through the app's use
   cases.
5. The **API** starts, and `aurora-fwd`/`cache-fwd` publish the datastores to `localhost`.

So a single `task docker:up` gives you a fully provisioned, migrated, seeded, host-reachable stack.

## Environment

```bash
cp .env.example .env     # gitignored; task env:create also seeds it
```

`.env` already points at the floci datastores (`DB_HOST=floci-rds-todo-aurora`,
`REDIS_HOST=floci-valkey-todo-redis`) and routes AWS at floci (`AWS_ENDPOINT_URL=http://floci:4566`).
`core/config.py` loads it into the Pydantic `Settings` that feed the root `ApplicationContainer`.

## Bootstrap + run

```bash
task env:create     # uv venv (Python 3.14) + sync dev/test/lint groups + seed .env
task docker:up      # ordered bring-up (floci → terraform → atlas → seed → API), then tails logs
task docker:down    # stop + clean caches
task docker:verify  # end-to-end check: app, Aurora, ElastiCache, schema, floci ECR/SSM
```

- **API (Swagger):** `http://localhost:8000/docs` — the live API reference.
- **Health:** `http://localhost:8000/health`.
- **Project docs (mkdocs):** `task docs:serve` → `http://127.0.0.1:8001` (this site).

## Connecting to the datastores

After `task docker:up` the datastores are on the host at the usual ports:

| Service | Host | Port | User | Password | DB |
|---|---|---|---|---|---|
| Aurora (Postgres) | `localhost` | `5432` | `todo` | `todopassword` | `todo` |
| ElastiCache (Valkey/Redis) | `localhost` | `6379` | — | — | — |

Quick shells: `task aurora:cli` (psql) · `task cache:cli` (valkey-cli).

## Entry points

Installed by `uv` as console scripts (used by the container and locally):

| Script | Purpose |
|---|---|
| `todo-api` | Serve the FastAPI app (uvicorn); `API_RELOAD=1` enables hot-reload |
| `todo-seed` | One-shot demo-data seeder (runs as the `seed` init container) |
| `todo-cli` | Admin/operational CLI (Typer) |

## Taskfile targets (selection)

| Target | Purpose |
|--------|---------|
| `env:create` | uv venv + sync dependency groups + seed `.env` |
| `check:linter` / `check:types` / `check:deadcode` | ruff / pyright / vulture |
| `check:quality` | ruff + pyright + vulture + coverage gate (≥ 97%) |
| `check:architecture` | import-linter contracts (layers + context boundaries) |
| `test:unit` / `test:integration` / `test:coverage` | test pyramid |
| `docker:up` / `docker:down` / `prune` / `docker:verify` | local stack lifecycle |
| `docker:shell` / `docker:logs` | shell / logs in the running stack |
| `atlas:migrate` / `atlas:status` / `atlas:new` / `atlas:hash` | DB migrations (Atlas) |
| `seed:demo` | re-run the demo-data seeder |
| `aurora:cli` / `cache:cli` | psql / valkey-cli on the datastores |
| `terraform:*` | cloud (Terragrunt) and `ENV=local` floci provisioning |
| `ecr:*` / `k8s:trivy` | image build/push + Helm scan |
| `docs:serve` / `docs:build` | the mkdocs documentation site |
| `clean:cache` | remove venv + tooling/infra caches |

## Typical inner loop

```bash
task check:quality        # lint + types + dead-code + coverage gate
task check:architecture   # layer + context boundary contracts
task test:unit            # fast feedback
```

The full pre-merge gate mirrors CI — see the `quality-gate` command
(`.claude/commands/quality-gate.md`) and the [Governance](governance.md) page.

## VSCode debugging

`.vscode/launch.json` provides debugger configs for the FastAPI app and `pytest`.
