# CI/CD (Gitea Actions)

In the local lab, CI/CD runs on **Gitea Actions** — the workflows under `.gitea/`. The merge →
build → push-to-ECR → deploy loop is reproduced end to end with **floci as the AWS backend** and
**floci-EKS as the compute** — k3s containers (`floci-eks-todo-app-<env>`) that emulate EKS. The
**platform (`local-gitops`) owns those clusters**: `task install` creates the dev/prod clusters and
bootstraps each with Argo CD and Grafana *before* this app deploys. The app pipeline provisions its
own cloud resources and **registers its Argo Applications onto the already-running cluster** — it does
not create the cluster or install Argo CD. Argo CD running inside each cluster is what reconciles each
deploy.

This page covers the local Gitea Actions pipeline. For what Argo does after a deploy, see
**[GitOps Deployment](gitops.md)**; for the chart it deploys, see **[Deployment](deployment.md)**;
for the floci Terraform stack the `terraform` job applies, see **[Infrastructure](infrastructure.md)**.

## The runner: `runs-on: lab`

Every workflow targets a host **`act_runner`** registered with the label `lab`. The runner uses
**host networking and the host Docker daemon**, and **bind-mounts the platform checkout at
`/opt/local-gitops`** — which is what makes the local pipeline work:

- floci is reachable at `http://localhost:4566` (so `aws --endpoint-url` and `docker push` to the
  floci ECR work);
- `task eks:load-image` imports the built image into the floci-EKS k3s containers directly (the k3s
  equivalent of `kind load`);
- the `cd` job calls the platform's tasks from `/opt/local-gitops` (`task eks:register-app`) to
  register the app onto the running cluster's Argo CD;
- `uv` and `task` are pinned to the same versions the `local-gitops` lab pins.

## Two workflows

| Workflow | Trigger | What it does | Touches |
|---|---|---|---|
| `ci-cd.yml` → job `ci` | push / PR to `main` (via `task gitea:ship`) | Quality gates + coverage (unit + integration; no Postgres) | nothing (gate only) |
| `ci-cd.yml` → job `terraform` | push to `main`, **after `ci`** | Static checks (fmt/validate/trivy) + `terragrunt apply ENV=dev` on floci | **dev floci infra** |
| `ci-cd.yml` → job `cd` | push to `main`, **after `terraform`** | Build → push to floci ECR → `eks:load-image` → bump `values-dev.yaml` → register Argo | **dev** |
| `promote.yml` | manual (`workflow_dispatch`, via `task gitea:promote`) | `terragrunt apply ENV=prod` → re-tag dev-proven image → `eks:load-image` → bump `values-prod.yaml` → register Argo | **prod** |

**One workflow, three chained jobs for DEV.** `ci`, `terraform` and `cd` all live in
`ci-cd.yml`, chained with `needs:` (`terraform` needs `ci`, `cd` needs `terraform`) — so the deploy
never runs unless lint, types, dead-code, architecture, the coverage suite *and* the infra apply pass
first. This is a single workflow (not several with `workflow_run`) because the lab's Gitea has no
reliable cross-workflow trigger; `needs:` is the portable way to order them. `terraform` and `cd` are
gated to `push` events (`if: github.event_name == 'push'`), so PRs run only `ci`.

The DEV pipeline is **AUTO** (every push to lab Gitea `main` via `task gitea:ship`); PROD is **MANUAL**
(`promote.yml` dispatched via `task gitea:promote`). Because the platform already created the prod
cluster at install time, only the **deploy** to prod is manual — there is no cluster to stand up.

### `ci` job — quality gate

Runs on pushes and PRs to `main`. After `uv sync` it runs, in order:

1. `task check:linter` (ruff)
2. `task check:types` (pyright)
3. `task check:deadcode` (vulture)
4. `task check:architecture` (import-linter contracts)
5. `task test:coverage` — unit + integration at the **≥ 97 %** gate

**No PostgreSQL or Docker is needed.** The suite is unit + integration only: the integration tier runs
on throwaway SQLite, and the RLS isolation test **self-skips** when `TEST_DATABASE_URL` is unset (it
cannot run on SQLite — see [Testing](../development/testing.md)). The FastAPI presentation layer is
covered by pure-unit tests that call handlers/middleware directly, so coverage holds at ≥ 97 % without
a live app or database. `concurrency` cancels superseded `ci` runs per ref. Prove tenant isolation by
running the suite against a real Postgres locally (`TEST_DATABASE_URL=… task test:integration`).

### `terraform` job — app cloud resources on floci

Runs **after `ci` passes** and **only on pushes**. It applies the per-environment Terragrunt stack
(`infra/terraform/environments/dev`, wired by `infra/terragrunt/dev`) against floci. Because the
modules that need a managed control plane or AWS-only service are **gated off on floci**
(`count = var.floci ? 0 : 1` — `vpc`, `eks`, `aurora`, `redis`, `cognito`, `cdn`, `route53`, `iam`),
the apply creates **only the app cloud resources** LocalStack can emulate: **ECR**, **Secrets
Manager**, **SQS/SNS**, **EventBridge**, **S3** and **Bedrock** scoping. `vpc`/`eks` are skipped
because **the platform owns the k3s cluster** and the app runs on in-cluster Postgres/Redis. Steps:

1. **Static checks** — `task terraform:fmt` (terraform fmt + terragrunt hcl), `task terraform:validate`
   (offline, no backend), `task terraform:trivy` (security scan).
2. **Restore state** — `aws s3 cp` the prior `terraform.tfstate` from floci S3 (`todo-app-tfstate-dev`);
   a fresh floci has none.
3. **`terragrunt apply ENV=dev`** (`AUTO_APPROVE=true`).
4. **Save state** back to floci S3 (`if: always()`), so successive runs don't re-create resources.

The app deploys but stays un-Healthy until these resources (and the secrets the chart reads) exist, so
this job runs **before** `cd`.

### `cd` job — continuous deploy to dev

Runs **only after `terraform`** and **only on pushes**. The `values-dev.yaml` bump it commits carries
`[skip ci]` (which Gitea honours), so the deploy commit cannot re-trigger the pipeline. Steps:

1. **Resolve tag** — `git rev-parse --short HEAD`.
2. **Build** the prod image — `docker build --target prod -t local/todo-app:<tag>`.
3. **Push to floci ECR** — logs in with `aws ecr get-login-password` against `localhost:4566`,
   creating the `todo-app` repo if absent, then `docker push`. **ECR is the registry of record** and
   the **artifact store for `promote`**, exactly as in the real cloud.
4. **`task eks:load-image ENV=dev`** — import the image into the floci-EKS **dev** k3s containerd
   (`ctr images import`; the k3s equivalent of `kind load`).
5. **Bump and commit** — `yq -i '.image.tag = "<tag>"' values-dev.yaml`, commit
   `ci: deploy <tag> to dev [skip ci]`, push to `main`. Done **before** registering Argo, so Argo's
   first sync targets the loaded tag (else the db-init Job wedges on `ImagePullBackOff`).
6. **Register the app with Argo** — `cd /opt/local-gitops && task eks:register-app ENV=dev
   APP_DIR=$GITHUB_WORKSPACE`, which applies this repo's `infra/k8s/gitops/applications/*.yaml`
   (`dependencies-dev`, `todo-app-dev`) onto the **already-running** dev cluster's Argo CD.

Argo CD on the dev cluster (running since `task install`) then reconciles the chart and rolls the
Deployment. PROD is never touched here — the job prints the manual handoff to `promote.yml`.

### `promote.yml` — manual promotion to prod

A `workflow_dispatch` job (dispatched via `task gitea:promote`) — **the only path that changes prod**.
It takes a `tag` already proven on dev (defaulting to whatever `values-dev.yaml` currently points at).
It mirrors the DEV shape but **does no build**:

1. **`terraform` job** — same static checks, then `terragrunt apply ENV=prod` on floci (app cloud
   resources only; the prod cluster already exists from `task install`), with its own
   `todo-app-tfstate-prod` state in floci S3.
2. **`cd` job**:
   - **Ensure the image is local** — if the build host has since pruned it, pull it back from floci
     ECR (the artifact the dev `cd` job pushed).
   - **`task eks:load-image ENV=prod`** into the floci-EKS **prod** containerd.
   - **Bump and commit** `values-prod.yaml` → `ci: promote <tag> to prod [skip ci]` → push.
   - **Register the app with Argo** — `cd /opt/local-gitops && task eks:register-app ENV=prod`.

Argo CD on the prod cluster syncs. Promotion ships the *same artifact* dev proved — it is never
rebuilt.

### `setup-lab` composite action

The `terraform`, `cd` and `promote` jobs share `.gitea/actions/setup-lab`, which installs the pinned
CLIs the lab jobs need — **aws**, **yq**, **kubectl**, **helm**, **terraform**, **terragrunt**,
**task** and **trivy** (`docker` and `git` already ship in the job image), versioned to track the lab.

## The full loop (`task gitea:ship` → live on dev)

```
platform (once): task install → floci-EKS dev + prod clusters + Argo CD + Grafana already running

task gitea:ship  (push to lab Gitea main)
   │
   ci-cd.yml
   │
   ├─ job ci ......... ruff · pyright · vulture · import-linter · coverage≥97% (unit+integration, no Postgres)
   │       │
   │       ▼ needs: ci
   ├─ job terraform .. fmt · validate · trivy · terragrunt apply ENV=dev (floci: ECR/Secrets/SQS-SNS/EventBridge/S3/Bedrock; EKS+VPC gated off)
   │       │
   │       ▼ needs: terraform
   └─ job cd ......... build (--target prod)
                       → docker push  → floci ECR  (todo-app, registry of record + artifact store)
                       → eks:load-image → floci-EKS dev k3s
                       → yq bump values-dev.yaml → commit "[skip ci]" → push main
                       → eks:register-app ENV=dev  (apply Argo Applications onto the running cluster)
                                │
                                ▼
                       Argo CD (dev, already running) reconciles → rolls the Deployment
                                │
                       manual: task gitea:promote → promote.yml
                                │
                                ▼
                       terragrunt apply ENV=prod  ·  eks:load-image → prod  ·  bump values-prod.yaml  ·  eks:register-app  ·  Argo CD (prod) syncs
```

## Local lab: from zero to deployed

The platform (`local-gitops`) installs **app-agnostic** — `task install` stands up the dev/prod
floci-EKS clusters with Argo CD and Grafana, but knows nothing about this app. The app
**self-onboards** into the running lab, then iterates with `gitea:ship`. `origin` stays the
**personal GitHub** repo (persistence + the `.github/` quality mirror); the lab Gitea repo is a
**separate push target** that the `runs-on: lab` runner watches.

```bash
# --- one time: build the platform (clusters + Argo CD + Grafana), then onboard the app ---
(cd ../local-gitops && task prune && task install)   # platform: creates floci-EKS dev+prod + Argo + Grafana
task prune                 # optional: clears the app's standalone docker stack
task gitea:create-repo     # create the empty Gitea repo in the lab
sudo task eks:hosts        # /etc/hosts: todo-app.dev.local → .230, todo-app.prod.local → .240
task gitea:ship            # DEV (auto): push → ci → terraform → cd → Argo deploys

# --- then iterate, N times, no reinstall ---
git commit -am "…" && task gitea:ship   # app change → DEV pipeline → Argo redeploys
task gitea:promote                      # PROD (manual): deploy the dev-proven tag to prod
task gitea:runs                         # recent Actions runs (UI link on Gitea < 1.23)
(cd ../local-gitops && task gitea:ship) # platform change → re-push platform config
```

The app's Argo Applications are **registered by the pipeline** (`eks:register-app`), so there is
nothing to register by hand here. `task argo:add-gitea-repo` is now just an informational notice. Until
the first `gitea:ship`, Argo shows the app's Applications as `Unknown`/`Failed` (empty repo) — they go
green once content is shipped.

`gitea:ship` targets `{GITEA_NS}/{GITEA_REPO_NAME}:{GITEA_BRANCH}` (lab defaults
`gitops/modular-monolithic-app:main`, Gitea at `gitea.dev.local`); override any as env vars for a
different lab. It is a **force push** because the `cd` job commits its own `values-*.yaml` bump back to
Gitea `main` — the lab copy is disposable and re-derived from your HEAD each ship, while GitHub stays
the source of truth.

## Local vs. real cloud

The pipeline is shaped to mirror production, with two honest local substitutions:

- **ECR push *and* `eks:load-image`.** The `docker push` to floci ECR reproduces the real
  pull-from-registry contract, but the floci-EKS k3s nodes aren't wired with `imagePullSecrets` for
  the floci registry, so the **`eks:load-image` step (a `ctr images import` into the cluster's
  containerd) is what actually makes the image runnable** locally. The chart uses
  `image.repository: local/todo-app` with `pullPolicy: IfNotPresent` accordingly. On real EKS, the
  node pulls the tag from ECR and the load step disappears.
- **floci-EKS k3s, not EKS.** There is no managed control plane locally — the platform's k3s
  containers stand in for EKS, and they (with Argo CD) come up at `task install`, before this app
  deploys. This app's `terraform` job therefore **skips** the `vpc`/`eks` modules on floci. See the
  [GitOps Deployment](gitops.md) "Local caveats" for the matching IRSA/Cognito/Bedrock no-ops.

On real EKS the same `.gitea/` workflows run unchanged against real AWS — the `terraform` job creates
the `vpc`/`eks` (and Aurora/Cognito/etc.) modules too, the node pulls the tag from ECR, and the
`eks:load-image` step simply falls away.
