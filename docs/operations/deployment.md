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
| `dev` | `dev-app` | Development environment |
| `prod` | `prod-app` | Production environment |

Each cluster has independent namespaces and per-namespace Kubernetes RBAC. Environment differences
are carried in `values-dev.yaml` vs `values-prod.yaml`.

## Local workflow ("floci")

`infra/k8s/gitops/` integrates with local-gitops to simulate the multi-cluster topology locally.
The infra layer has its own tests under `infra/tests/` (Terratest, Trivy). A successful local
install means `helm install` against a local kind/k3d cluster wired via local-gitops, with the DB
init Job completing before API pods report ready.
