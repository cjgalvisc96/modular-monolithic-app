# GitOps integration — `local-gitops`

The TODO service is deployed **GitOps-driven via Argo CD** on the
[`local-gitops`](https://github.com/cjgalvisc96/local-gitops) platform — three
`kind` clusters (management / dev / prod), Gitea as the in-cluster Git server,
floci as the local AWS, and a per-cluster Argo CD running an **app-of-apps**
that recurses `platform-config/envs/<env>`.

CI builds, tests, and plans infra — it never deploys. Deployment is pull-based:
Argo CD reconciles this repo's Helm chart onto the clusters.

## The contract: the app is self-contained, the platform is generic

Everything app-specific lives **here**, so onboarding the platform stays a
near-zero, repeatable change (the same shape for every future app):

| Concern | Where it lives | File(s) |
|---|---|---|
| API workload, SAs, RBAC, db-init | this repo's Helm chart | `infra/k8s/helm/` |
| Namespace | Argo CreateNamespace + chart `namespaceConfig` | `infra/k8s/helm/templates/namespace.yaml` |
| Datastores (local Postgres/Redis) | this repo, synced as its own Application | `infra/k8s/dependencies/base/` |
| Secrets in floci SSM + ECR repo | this repo's seed script | `infra/k8s/gitops/floci-seed.sh` |
| Argo registration | this repo's Application manifests | `infra/k8s/gitops/applications/` |

The platform contributes only generic primitives: clusters, Argo CD, the ESO
`aws-ssm` ClusterSecretStore, ingress-nginx, DNS, floci, and the Gitea mirror.
It contains **no `todo-app` knowledge**.

## What's here

| File | Purpose |
|---|---|
| `applications/todo-app-{dev,prod}.yaml` | The app `Application` (sync-wave 2) — Helm chart at `infra/k8s/helm`, `values-<env>.yaml`. |
| `applications/dependencies-{dev,prod}.yaml` | The datastores `Application` (sync-wave 1) — synced before the app so Postgres/Redis are healthy before the Atlas db-init hook. |
| `floci-seed.sh` | Idempotently seeds `/gitops/<env>/todo-app/{DB_USER,DB_PASSWORD,REDIS_PASSWORD}` and the `gitops/todo-app` ECR repo into floci. |

The chart aligns to every platform convention: namespace `todo-app`, secrets via
an `ExternalSecret` reading the platform's `aws-ssm` ClusterSecretStore, ingress
`todo-app.<env>.local` on `nginx`, Prometheus scrape annotations, and the AWS
SDK pointed at floci (`AWS_ENDPOINT_URL=http://172.18.0.1:4566`).

## Onboarding into the platform (the minimal change "there")

1. **Register the repo for mirroring + image build.** Point the platform at this
   repo:
   ```bash
   DEPLOY_APP=true \
   APP_REPO_NAME=modular-monolithic-app \
   APP_REPO_PATH=$(pwd) \
   APP_IMAGE=local/todo-app \
   ./install.sh            # or: task install:app
   ```
   `install.sh` mirrors the repo into Gitea, builds `local/todo-app:{dev,prod}`
   into the kind clusters, and runs this repo's `floci-seed.sh`.

2. **Drop the four Application manifests** into the platform's control repo so
   the root app-of-apps adopts them:
   ```bash
   cp infra/k8s/gitops/applications/*-dev.yaml   <local-gitops>/platform-config/envs/dev/
   cp infra/k8s/gitops/applications/*-prod.yaml  <local-gitops>/platform-config/envs/prod/
   ```

3. **Allow-list this repo** in each env's `AppProject`
   (`platform-config/envs/<env>/project.yaml`) — one line under `sourceRepos`:
   ```yaml
   - http://172.18.255.209:3000/gitops/modular-monolithic-app.git
   ```

That's the whole platform-side footprint: a repo registration + four manifests +
one `sourceRepos` line per env. Argo CD's `directory.recurse` discovers the rest.
(The `172.18.*` address is the platform's default kind-bridge Gitea LB IP;
`local-gitops` rewrites the prefix via `subst_net` if its subnet differs.)

## Seeding floci by hand (outside `install.sh`)

```bash
AWS_ENDPOINT_URL=http://localhost:4566 AWS_PROFILE=floci \
  ./infra/k8s/gitops/floci-seed.sh          # or: task gitops:seed-floci
```

## Local caveats (kind, not AWS)

None apply to a real EKS deploy:

- **IRSA annotations are no-ops** — `eks.amazonaws.com/role-arn` needs an AWS
  OIDC provider; on kind they're ignored.
- **AWS-backed features are inert** — Cognito, Bedrock, and Aurora IAM auth have
  no local backend. Use the DEBUG dev-auth header and the `StubLlmClient`
  (`DEBUG=true`); `DB_*`/`REDIS_*` point at the in-namespace Postgres/Redis.
- **RLS still works** — it's pure PostgreSQL, so tenant isolation is real locally.
