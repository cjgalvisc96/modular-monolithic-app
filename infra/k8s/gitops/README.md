# GitOps integration — local full-platform testing (`local-gitops`)

Deployment of the TODO service is **GitOps-driven via Argo CD**, exercised
locally on the [`local-gitops`](https://github.com/cjgalvisc96/local-gitops)
platform — a fully local lab that stands up three `kind` clusters
(management / dev / prod), Gitea as the in-cluster Git server, and Argo CD in
an app-of-apps topology. This is the "floci" local multi-cluster simulation the
plan calls for: it tests the whole deploy path end-to-end on your machine, no
cloud account required.

CI (GitHub Actions) **builds, tests, and plans infra** — it never deploys.
Deployment is pull-based: Argo CD reconciles the manifests below onto the
dev/prod clusters.

## What's here

| File | Purpose |
|---|---|
| `project.yaml` | Argo CD `AppProject` **todo-app** — whitelists this repo as a source and the dev/prod clusters as destinations. Self-contained, so it needs no edits to the platform's restricted `dev`/`prod` projects. |
| `applicationset.yaml` | Argo CD `ApplicationSet` **todo-app** — a cluster generator (same style as the platform's own `applications` set) that renders one `Application` per registered cluster, deploying the Helm chart (`infra/k8s/helm`) with `values-<env>.yaml`. |

The chart deploys to namespace `dev-app` / `prod-app`, with three IRSA service
accounts and the DB-init Job as a Helm `pre-install`/`pre-upgrade` hook (Argo
CD's hook engine runs it as a `PreSync` step, before the API Deployment reports
healthy — migrate first, then roll the API).

## How it maps to the `local-gitops` platform

The platform's own `applications` ApplicationSet enumerates kustomize overlays
in the Gitea-hosted `gitops-apps` repo. This service instead ships its **own
Helm chart in its own repo**, so it's wired as a dedicated project +
ApplicationSet that source from this repo. The conventions are kept identical:

- destination `name: dev|prod` — the cluster names `local-gitops` registers
- an `environment` cluster-label selector — the same generator the platform uses
- `gitops.local/env` + `gitops.local/app` labels
- `repoURL` = the in-cluster Gitea mirror (`gitops/modular-monolithic-app.git`)

## Wiring it in

1. **Mirror this repo into Gitea** so in-cluster Argo CD can reach it: seed
   `modular-monolithic-app` into the platform's Gitea under
   `gitops/modular-monolithic-app.git` (where `gitops-apps` already lives). To
   pull from GitHub instead, change `repoURL` in `applicationset.yaml` to the
   GitHub URL and add repo creds in Argo CD — both URLs are already allow-listed
   in `project.yaml`.

2. **Build the image into the kind clusters** (no external registry locally):
   ```bash
   docker build --target prod -t local/todo-app:dev .
   kind load docker-image local/todo-app:dev --name dev
   kind load docker-image local/todo-app:dev --name prod
   ```

3. **Register the project + ApplicationSet** — either commit them under the
   platform's `platform-config/` so the root app-of-apps adopts them, or apply
   to the management cluster directly:
   ```bash
   kubectl --context kind-management apply -f infra/k8s/gitops/project.yaml
   kubectl --context kind-management apply -f infra/k8s/gitops/applicationset.yaml
   argocd app list          # → todo-app-dev, todo-app-prod
   ```

## Local caveats (kind, not AWS)

Expected when testing on the local platform — none apply to a real EKS deploy:

- **IRSA annotations are no-ops.** The `eks.amazonaws.com/role-arn` annotations
  on the service accounts need an AWS OIDC provider; on kind they're ignored.
- **AWS-backed features are inert.** Cognito, Bedrock, and Aurora IAM auth have
  no local backend. Use the API's DEBUG dev-auth header (`X-Dev-Tenant`) for
  auth and the `StubLlmClient` (active when `DEBUG=true`) for AI — the same
  paths the e2e tests use. Point `DB_*` / `REDIS_*` at in-cluster Postgres/Redis
  via `values-dev.yaml`.
- **RLS still works** — it's pure PostgreSQL, so tenant isolation is real even
  locally.
