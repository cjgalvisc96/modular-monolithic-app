# Infrastructure

Cloud infrastructure is defined with **Terraform** modules, composed per environment with
**Terragrunt** for DRY configuration. Everything lives under `infra/terraform/` and
`infra/terragrunt/`.

## Terraform modules

`infra/terraform/modules/` holds one module per concern:

| Module | Purpose |
|--------|---------|
| `vpc` | Network — public and private subnets |
| `eks` | Kubernetes control plane + node groups |
| `ecr` | Container image registry |
| `redis` | Cache layer |
| `aurora` | PostgreSQL (public + private subnets) |
| `route53` | DNS |
| `secrets-manager` | DB credentials, Cognito client secrets — never hardcoded |
| `cognito` | Single User Pool, app client, pre-token Lambda (injects `tenant_id` + role claims), groups for RBAC |
| `cdn` | Content delivery |
| `s3` | Object storage |
| `eventbridge` | Background/async event routing |
| `sqs-sns` | Queues / notifications |
| `bedrock` | AI capability consumed by the `ai` context |
| `iam` | Least-privilege IRSA roles (see below) |

## Cognito module

`modules/cognito/` provisions the identity layer that backs the whole tenancy and auth chain:

- `main.tf` — the User Pool and app client.
- `groups.tf` — RBAC groups (roles) per permission tier.
- `pre_token_lambda/` — the pre-token-generation Lambda that injects the `tenant_id` custom claim
  and role/group claims into every issued JWT.

This is the source of the `tenant_id` claim that drives PostgreSQL RLS — see
[Multi-Tenancy](../architecture/multi-tenancy.md) and
[ADR-0002](../adr/0002-cognito-over-keycloak.md).

## IAM module (least privilege via IRSA)

`modules/iam/` defines one narrowly scoped role per workload, each as a discrete file reviewed
independently of the resources it grants access to:

- `api_pod_role.tf` — Aurora (IAM DB auth) + scoped Secrets Manager read.
- `ai_pod_role.tf` — `bedrock:InvokeModel` only, scoped to specific model ARNs.
- `db_init_job_role.tf` — DDL + Secrets Manager read; no runtime data access.
- `eventbridge_role.tf` — publish-only to a specific event bus.

Rationale: [ADR-0006](../adr/0006-least-privilege-iam-irsa.md).

## Environments and Terragrunt

```
infra/terraform/environments/{dev,prod}   # environment-specific module composition
infra/terragrunt/{dev,prod}               # DRY environment wiring
```

Terragrunt keeps the `dev` and `prod` compositions DRY, sharing module definitions while varying
inputs per environment. Secrets are always sourced from Secrets Manager, never hardcoded.

## Local simulation (floci)

For local development the AWS services floci can emulate are provisioned by a dedicated Terraform
stack, `infra/terraform/local` (`task terraform:apply ENV=local`): the **ECR** repo, **SSM**
parameters, an **Aurora** (RDS Postgres) cluster and an **ElastiCache** (Redis) replication group —
floci backs the datastores with real `postgres`/`valkey` containers on the compose network.

`task docker:up` provisions that stack, then runs the **Atlas migration** and **demo-data seed** as
one-shot init containers before the API — the same "DB init decoupled from API startup" rule as the
Helm Job ([Deployment](deployment.md)). The managed control-plane services the cloud stacks use
(VPC, EKS, CloudFront, Cognito, Route53) cannot run on floci and are absent locally.

## Infrastructure tooling

| Tool | Role |
|------|------|
| `terraform validate` | Syntax/configuration validation |
| **Terratest** | Automated infrastructure tests (`infra/tests/terratest/`) |
| **Trivy** | Security scanning, incl. confirming no IAM role is broader than scoped (`infra/tests/trivy/`) |
| **Infracost** | Cost estimation per PR |

The bar: `terragrunt plan` succeeds for both `dev` and `prod` with zero `terraform validate` errors
and no critical Trivy findings, with an Infracost report generated per pull request.
