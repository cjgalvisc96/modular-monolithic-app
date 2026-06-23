# Deployment

The application is deployed to **Kubernetes (EKS)** with a **Helm chart**. The local DevOps
workflow ("floci") mirrors production using a local multi-cluster setup via
[local-gitops](https://github.com/cjgalvisc96/local-gitops).

## Helm chart

The chart lives at `infra/k8s/helm/`:

```
infra/k8s/helm/
├── Chart.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── deployment.yaml       # API Deployment (multiple replicas)
    ├── service.yaml
    ├── job-db-init.yaml      # DB init/migrations as an independent Job
    ├── rbac.yaml             # cluster-internal Kubernetes RBAC
    ├── service-account.yaml  # IRSA-annotated service accounts
    └── namespace.yaml
```

The chart is fully declarative — namespace, service account, deployment, service, RBAC, and the DB
init Job are all expressed as templates parameterized by environment values.

## DB init as a separate Job

Database initialization and Atlas migrations run as a **separate Kubernetes `Job`**
(`job-db-init.yaml`), **not** from API container startup. The Job runs via a Helm hook
(`pre-install` / `pre-upgrade`) so it completes **before** API pods report ready. This avoids
migration races across API replicas. The rationale is in
[ADR-0005](../adr/0005-db-init-as-separate-job.md).

## IRSA service accounts

Each workload binds to its own least-privilege IAM role via **IRSA**, through annotated service
accounts in `service-account.yaml`:

| Workload | IAM role scope |
|----------|----------------|
| API pod | Aurora (IAM DB auth) + read-only its specific Secrets Manager secrets |
| AI pod | `bedrock:InvokeModel` on specific model ARNs only |
| DB-init Job | DDL execution + Secrets Manager read; no runtime data access |
| EventBridge publisher | publish-only to a specific event bus |

No workload uses a shared or account-wide role. See
[ADR-0006](../adr/0006-least-privilege-iam-irsa.md) and [Infrastructure](infrastructure.md).

## Multi-cluster topology

| Cluster | Namespace | Purpose |
|---------|-----------|---------|
| `dev` | `todo-app` (dev cluster) | Development environment |
| `prod` | `todo-app` (prod cluster) | Production environment |

Each cluster has independent namespaces and per-namespace Kubernetes RBAC. Environment differences
are carried in `values-dev.yaml` vs `values-prod.yaml`.

## Local workflow ("floci")

`infra/k8s/gitops/` integrates with [local-gitops](https://github.com/cjgalvisc96/local-gitops),
which stands up `kind` dev/prod clusters, each running its own Argo CD as an **app-of-apps** that
recurses `platform-config/envs/<env>`. Deployment is pull-based: Argo CD reconciles this repo's Helm
chart; CI never deploys.

**The app is self-contained; the platform is generic.** Everything app-specific lives in this repo,
so onboarding the platform is a near-zero, repeatable change — the same shape for every future app:

| Concern | Where | Files |
|---|---|---|
| Argo registration | this repo | `infra/k8s/gitops/applications/{todo-app,dependencies}-{dev,prod}.yaml` |
| API workload + db-init + IRSA SAs + RBAC + namespace | the Helm chart | `infra/k8s/helm/` |
| Local datastores (Postgres/Redis) | this repo | `infra/k8s/dependencies/base/` |
| floci SSM params + ECR repo | this repo | `infra/k8s/gitops/floci-seed.sh` (`task gitops:seed-floci`) |

The two **Applications** order the rollout: the datastores Application (`sync-wave 1`) becomes
healthy before the app Application (`sync-wave 2`), so Postgres exists before the chart's
`pre-install` db-init hook runs migrations. The platform contributes only generic primitives
(clusters, Argo CD, the ESO `aws-ssm` store, ingress, DNS, floci, Gitea) and carries **no
`todo-app` knowledge**. The whole platform-side footprint per app is its Application manifests in
`platform-config/envs/<env>/` plus one `sourceRepos` line. The full contract is in
[`infra/k8s/gitops/README.md`](https://github.com/cjgalvisc96/modular-monolithic-app/tree/master/infra/k8s/gitops).

For a lighter loop, the docker-compose stack (`task docker:up`) reproduces the same ordering with
**init containers**: an `atlas` container runs the migrations and a `seed` container loads demo data
(`todo_app/scripts/seed.py`), both completing before the API container starts — mirroring the Helm
DB-init Job. The image exposes the `todo-api` (serve) and `todo-seed` (seed) entry points. See
[Development Setup](../development/setup.md).
