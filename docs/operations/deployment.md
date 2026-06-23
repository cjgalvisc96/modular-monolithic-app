# Deployment

The application is deployed to **Kubernetes (EKS)** with a **Helm chart**. The local DevOps
workflow ("floci") mirrors production using a local multi-cluster setup via
[local-gitops](https://github.com/cjgalvisc96/local-gitops).

## Helm chart

The chart lives at `infra/k8s/helm/`:

```
infra/k8s/helm/
├── Chart.yaml
├── values.yaml              # base values
├── values-dev.yaml          # dev overrides
├── values-prod.yaml         # prod overrides
├── NOTES.txt
└── templates/
    ├── _helpers.tpl
    ├── namespace.yaml        # app owns its namespace (toggle via namespaceConfig.create)
    ├── service-account.yaml  # IRSA-annotated service accounts
    ├── rbac.yaml             # cluster-internal Kubernetes RBAC
    ├── configmap.yaml        # non-secret app config
    ├── secret.yaml           # in-cluster secret (local/dev)
    ├── externalsecret.yaml   # ESO pull from the aws-ssm store (floci/SSM)
    ├── job-db-init.yaml      # DB init/migrations as an independent Job (Helm hook)
    ├── deployment.yaml       # API Deployment (multiple replicas)
    ├── service.yaml
    ├── ingress.yaml
    └── hpa.yaml              # horizontal pod autoscaler
```

The chart is fully declarative — namespace, service account, deployment, service, RBAC, config,
secrets (in-cluster and via ESO), and the DB init Job are all expressed as templates parameterized
by environment values. The app **owns its namespace** (created by the chart, or by Argo CD's
`CreateNamespace` when `namespaceConfig.create=false`), so the GitOps platform stays app-agnostic.

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
are carried in `values-dev.yaml` vs `values-prod.yaml` — which the [CI/CD](cicd.md) pipelines bump
(dev on merge, prod on manual promote) for Argo CD to reconcile.

## Local workflow ("floci")

`infra/k8s/gitops/` integrates with [local-gitops](https://github.com/cjgalvisc96/local-gitops)
to simulate the multi-cluster topology locally: pull-based Argo CD (app-of-apps), the app's own
Helm chart and datastores, secrets via the ESO `aws-ssm` store, and floci as the local AWS. The app
is self-contained and the platform stays generic, so onboarding is a near-zero, repeatable change.
See **[GitOps Deployment](gitops.md)** for the full contract and onboarding steps.

For a lighter loop, the docker-compose stack (`task docker:up`) reproduces the same ordering with
**init containers**: an `atlas` container runs the migrations and a `seed` container loads demo data
(`todo_app/scripts/seed.py`), both completing before the API container starts — mirroring the Helm
DB-init Job. The image exposes the `todo-api` (serve) and `todo-seed` (seed) entry points. See
[Development Setup](../development/setup.md).
