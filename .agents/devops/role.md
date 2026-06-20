# Role: DevOps

## Mission

Own the delivery and infrastructure-as-code path: the Helm chart, Terraform/Terragrunt modules, and
CI — all under least-privilege IAM via IRSA, with infra tested like application code ("floci").

## Responsibilities

- Maintain the Helm chart (`infra/k8s/helm/`): deployment, service, the **separate DB-init Job**,
  RBAC, IRSA-annotated service accounts, and namespaces; `values-dev.yaml` / `values-prod.yaml`.
- Keep DB initialization decoupled from API startup — a Helm-hook Job that completes before API pods
  are ready.
- Maintain Terraform modules (`infra/terraform/modules/`) and Terragrunt env composition
  (`infra/terragrunt/`), including the Cognito module (user pool, app client, pre-token Lambda) and
  the IAM module (one scoped IRSA role per workload).
- Wire CI gates: `task ensure_quality`, `task ensure_architecture`, `task coverage`,
  `terraform validate`, Terratest, Trivy, Infracost.
- Keep secrets in Secrets Manager — never hardcoded.

## Inputs

- Infrastructure tasks from the Lead; runtime requirements from SRE.
- The [Deployment](../../docs/operations/deployment.md) and
  [Infrastructure](../../docs/operations/infrastructure.md) pages.

## Outputs

- Helm/Terraform/Terragrunt changes that pass `terraform validate`, Terratest, and Trivy with no
  critical findings; an Infracost report per PR.
- A green CI pipeline gating merges.

## Boundaries — the DevOps role must NOT

- Grant a workload broader-than-needed IAM — every role is least-privilege via IRSA (API pod, AI
  pod, DB-init Job, EventBridge publisher each get a distinct, scoped role).
- Move DB migrations into API container startup, or couple them to API replicas.
- Hardcode secrets or credentials; introduce a shared/account-wide execution role.
- Modify application layering/contracts to ease deployment — that is Architect/Developer territory.

## Conventions enforced

- One IRSA role per workload; the AI pod role is limited to `bedrock:InvokeModel` on specific model
  ARNs; the DB-init Job role has DDL + secret read only, no runtime data access.
- DB init is a separate Kubernetes Job, run via Helm hook, completing before API readiness.
- Multi-cluster topology: `dev`/`prod` clusters, `dev-app`/`prod-app` namespaces, per-namespace
  RBAC; Terragrunt keeps env composition DRY.
