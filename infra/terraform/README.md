# Cloud Infrastructure (Terraform + Terragrunt)

AWS infrastructure for the multi-tenant TODO SaaS: a DDD modular monolith running
on EKS, fronted by Cognito, backed by Aurora PostgreSQL (RLS multi-tenancy), with
Bedrock-powered AI and least-privilege IRSA per workload.

- Terraform `>= 1.5`, AWS provider `~> 5.0`.
- Two environments: **dev** and **prod**.
- Reference modules: they `terraform validate` cleanly; they are not guaranteed to
  `apply` without real account context (domains, model availability, etc.).

## Layout

```
infra/terraform/
  modules/        # reusable building blocks (one concern each)
    vpc/            VPC, public/private subnets across AZs, IGW, NAT, route tables
    eks/            EKS cluster + managed node group + OIDC provider (IRSA) + aws-auth
    ecr/            ECR repo, scan-on-push, lifecycle policy
    redis/          ElastiCache Redis replication group, private subnet group, SG
    aurora/         Aurora PostgreSQL, IAM DB auth ENABLED, param group, SGs, subnet groups
    route53/        Hosted zone + records (alias-aware)
    secrets-manager/ DB creds + Cognito client secret
    cognito/        Single User Pool, app client, domain, custom:tenant_id,
                    RBAC groups, pre-token-generation Lambda (claims injection)
    cdn/            CloudFront distribution + OAC in front of S3
    s3/             Buckets: public access block, versioning, encryption
    eventbridge/    Custom event bus for async/background tasks
    sqs-sns/        SNS topic + SQS queue (+ DLQ) + subscription
    bedrock/        Scopes allowed model IDs, outputs model ARNs
    iam/            Least-privilege IRSA roles (see below)
  environments/
    dev/            Composes modules with dev sizing
    prod/           Composes modules with prod sizing (larger, multi-AZ)
```

Terragrunt (`infra/terragrunt/`) wraps the environments for DRY remote state and
provider generation — see `infra/terragrunt/README.md`.

## IRSA least-privilege summary

IRSA depends on the EKS OIDC provider (created in the `eks` module). Every role's
trust policy is an `sts:AssumeRoleWithWebIdentity` scoped to **one** Kubernetes
service account via `<oidc>:sub = system:serviceaccount:<namespace>:<sa>` and
`<oidc>:aud = sts.amazonaws.com`. Namespace is `todo-app` (clusters are per-environment).

| Role (file)               | Service account     | Permissions (and nothing else)                                              |
|---------------------------|---------------------|------------------------------------------------------------------------------|
| `api_pod_role.tf`         | `todo-app-api`      | `rds-db:connect` on the specific DB user ARN + `GetSecretValue` on ITS secrets |
| `ai_pod_role.tf`          | `todo-app-ai`       | `bedrock:InvokeModel` (+ stream) on specific model ARN(s) only — no S3, no `bedrock:*` |
| `db_init_job_role.tf`     | `todo-app-db-init`  | `rds-db:connect` as the migrator user + migration secret read — NO app-data access |
| `eventbridge_role.tf`     | `todo-app-api`      | `events:PutEvents` to ONE bus ARN — publish only, no subscribe/manage         |

The four role ARNs are exported and consumed by the Helm chart's service-account
`eks.amazonaws.com/role-arn` annotations.

## Other correctness guarantees

- **EKS OIDC provider** enabled (required for IRSA).
- **Aurora**: `iam_database_authentication_enabled = true`, `rds.force_ssl`.
- **Cognito**: single pool, `custom:tenant_id` attribute, pre-token Lambda injects
  `tenant_id` + `role` + `groups` claims; RBAC groups `admin` / `member`.
- **Secrets** sourced from Secrets Manager — never hardcoded; passwords arrive via
  `TF_VAR_db_master_password`.
- **S3** buckets: public access blocked, versioned, encrypted, OAC-only access.

## Tooling

Common variables include a `tags` map (`Owner` / `Environment` / `Project`).

```bash
# Format
terraform fmt -recursive infra/terraform infra/terragrunt

# Validate a module in isolation (no AWS creds needed)
terraform -chdir=infra/terraform/modules/iam init -backend=false
terraform -chdir=infra/terraform/modules/iam validate

# Plan/apply an environment via Terragrunt
cd infra/terragrunt/dev && terragrunt plan
```

| Tool        | Purpose                                                        |
|-------------|---------------------------------------------------------------|
| `terraform validate` | Static configuration validation per module/environment |
| **Terratest** | Go integration tests that spin up + assert real resources    |
| **Trivy**    | IaC security/misconfiguration scanning (`trivy config infra/`) |
| **Infracost** | Cost estimation of plans across dev/prod                      |
