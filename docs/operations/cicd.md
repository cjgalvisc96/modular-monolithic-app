# CI/CD (Gitea Actions)

In the local lab, CI/CD runs on **Gitea Actions** — the workflows under `.gitea/`. The merge →
build → push-to-ECR → deploy loop is reproduced end to end with **floci as the AWS backend** and
**`kind` as the compute** — there is no EKS; Argo CD running inside the `kind` clusters is what
reconciles each deploy.

This page covers the local Gitea Actions pipeline. For what Argo does after a commit lands, see
**[GitOps Deployment](gitops.md)**; for the chart it deploys, see **[Deployment](deployment.md)**;
for the floci Terraform stack the infra workflow applies, see **[Infrastructure](infrastructure.md)**.

## The runner: `runs-on: lab`

Every workflow targets a host **`act_runner`** registered with the label `lab`. The runner uses
**host networking and the host Docker daemon**, which is what makes the local pipeline work:

- floci is reachable at `http://localhost:4566` (so `aws --endpoint-url` and `docker push` to the
  floci ECR work);
- `kind load docker-image` reaches the `kind` node containers directly;
- `uv` and `task` are pinned to the same versions the `local-gitops` lab pins (`mise.toml`).

## Four workflows

| Workflow | Trigger | What it does | Touches |
|---|---|---|---|
| `ci.yml` | push / PR to `main` | Quality gates + coverage on a real Postgres | nothing (gate only) |
| `tf-floci.yml` | push to `main` (`infra/terraform/local/**`) or manual | `terraform apply` the floci stack — ECR repo + SSM params | **floci infra** |
| `cd.yml` | push to `main` | Build → push to floci ECR → `kind load` → bump `values-dev.yaml` | **dev** |
| `promote.yml` | manual (`workflow_dispatch`) | Re-tag a dev-proven image → `kind load` → bump `values-prod.yaml` | **prod** |

The dependency order is **infra → build/push → promote**: `tf-floci` provisions the
`gitops/todo-app` ECR repo `cd.yml` pushes to and the `/gitops/<env>/todo-app/*` SSM params the
app's `ExternalSecret` reads. The `local-gitops` `install.sh` applies the **same** Terraform stack at
bootstrap, so a fresh lab already has the infra; `tf-floci` is for ongoing changes. Both share state
in floci S3, so neither re-creates the other's resources.

### `ci.yml` — quality gate

Runs on pushes and PRs to `main` (scoped to `src/`, `tests/`, `migrations/`, `pyproject.toml`,
`uv.lock`, and the workflow itself). After `uv sync` it runs, in order:

1. `task check:linter` (ruff)
2. `task check:types` (pyright)
3. `task check:deadcode` (vulture)
4. `task check:architecture` (import-linter contracts)
5. Starts a **real PostgreSQL** (`postgres:16-alpine` on `:55432`, exposed via `TEST_DATABASE_URL`)
6. `task test:coverage` — the full suite at the **≥ 97 %** gate

Because a real Postgres is up, the **RLS isolation test runs for real** (it cannot run on SQLite —
see [Testing](../development/testing.md)). `concurrency` cancels superseded runs per ref; the job is
read-only (`permissions: contents: read`).

### `tf-floci.yml` — infrastructure (floci)

Applies `infra/terraform/local` against floci — the **Terraform-native** seeder for the ECR repo and
the `/gitops/<env>/todo-app/*` SSM parameters (the stack also declares the Aurora/ElastiCache
datastores; in the `kind` lab those are unused and may no-op). Runs on push to `main` touching
`infra/terraform/local/**`, or manually (`workflow_dispatch` with `plan`/`apply`/`destroy`). Steps:

1. **Restore state** — `aws s3 cp` the prior `terraform.tfstate` from floci S3 (the stack already
   points its `s3` endpoint at floci); a fresh floci has none.
2. **`terraform init` + the chosen action** via `task terraform:* ENV=local`, with
   `TF_VAR_floci_endpoint` and `TF_VAR_repository_name=gitops/todo-app`.
3. **Save state** back to floci S3, so the next run — and the `local-gitops` `install.sh`, which
   applies the **same** stack at bootstrap — share one state and don't fight over resources.

Because `install.sh` seeds at bootstrap, you normally only run this manually for an infra change. Run
it (or install) **before** the first `cd.yml`, or the app deploys but stays un-Healthy until the SSM
params exist.

### `cd.yml` — continuous deploy to dev

Runs on every push to `main` that touches image-affecting paths (`src/`, `migrations/`,
`Dockerfile`, `pyproject.toml`, `uv.lock`, the workflow, and the `setup-lab` action). The
`values-dev.yaml` bump it commits is **deliberately excluded** from the trigger paths, so the deploy
commit cannot re-trigger the workflow. Steps:

1. **Resolve tag** — `git rev-parse --short HEAD`.
2. **Build** the prod image — `docker build --target prod -t local/todo-app:<tag>`.
3. **Push to floci ECR** — logs in with `aws ecr get-login-password` against `localhost:4566`,
   creating the `gitops/todo-app` repo if absent, then `docker push`. **ECR is the registry of
   record**, exactly as in the real cloud.
4. **`kind load`** the image into the **dev** cluster.
5. **Bump and commit** — `yq -i '.image.tag = "<tag>"' values-dev.yaml`, commit
   `ci: deploy <tag> to dev [skip ci]`, and push back to `main` (using `github.token`).

Argo CD on the dev cluster then sees the new `values-dev.yaml` commit and rolls the Deployment to
the new tag. PROD is never touched here.

### `promote.yml` — manual promotion to prod

A `workflow_dispatch` job — **the only path that changes prod**. It takes a `tag` already proven on
dev (defaulting to whatever `values-dev.yaml` currently points at) and does **no build**:

1. **Ensure the image is local** — if the dev build host has since pruned it, pull it back from the
   floci ECR (the artifact built by `cd.yml` lives there).
2. **`kind load`** it into the **prod** cluster.
3. **Bump and commit** `values-prod.yaml` → `ci: promote <tag> to prod [skip ci]` → push.

Argo CD on the prod cluster syncs. Promotion ships the *same artifact* dev proved — it is never
rebuilt.

### `setup-lab` composite action

`cd.yml` and `promote.yml` share `.gitea/actions/setup-lab`, which installs the pinned CLIs the lab
jobs need — **kind**, **yq**, **aws** (`docker` and `git` already ship in the job image), versioned
to track the lab.

## The full loop (merge an MR → live on dev)

```
infra first: install.sh (bootstrap) or tf-floci ... terraform apply → ECR repo + SSM params (floci)

merge to main
   │
   ├─ ci.yml ........ ruff · pyright · vulture · import-linter · coverage≥97% (real Postgres → RLS runs)
   │
   └─ cd.yml ........ build (--target prod)
                      → docker push  → floci ECR  (gitops/todo-app, registry of record)
                      → kind load    → dev cluster
                      → yq bump values-dev.yaml → commit "[skip ci]" → push main
                                │
                                ▼
                      Argo CD (dev) reconciles the commit → rolls the Deployment
                                │
                      manual: promote.yml (workflow_dispatch)
                                │
                                ▼
                      kind load → prod  ·  bump values-prod.yaml  ·  Argo CD (prod) syncs
```

## Local vs. real cloud

The pipeline is shaped to mirror production, with two honest local substitutions:

- **ECR push *and* `kind load`.** The `docker push` to floci ECR reproduces the real
  pull-from-registry contract, but `kind` nodes aren't wired with `imagePullSecrets` for the floci
  registry, so the **`kind load` step is what actually makes the image runnable** locally. The chart
  uses `image.repository: local/todo-app` with `pullPolicy: IfNotPresent` accordingly. On real EKS,
  the node pulls the tag from ECR and the load step disappears.
- **`kind`, not EKS.** There is no managed control plane locally. The `kind-dev` / `kind-prod`
  clusters run Argo CD, which reconciles the `values-*.yaml` commits the workflows push. See the
  [GitOps Deployment](gitops.md) "Local caveats" for the matching IRSA/Cognito/Bedrock no-ops.

On real EKS the same `.gitea/` workflows run unchanged against real AWS — the node pulls the tag
from ECR and the `kind load` step simply falls away.
