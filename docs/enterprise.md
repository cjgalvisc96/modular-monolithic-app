# Enterprise Readiness

The production target for this application is a **full deployment on a real AWS account**.
floci (LocalStack) is only the local inner-loop emulator — `var.floci=true` gates off the AWS
services LocalStack cannot run and substitutes in-cluster Postgres/Redis plus DEBUG dev-auth.
The complete, phase-by-phase roadmap is `enterpise-plan.md` at the repository root.

## Target AWS architecture

| Pillar | AWS services |
|--------|--------------|
| Identity | Amazon Cognito — user pool, app clients, groups → roles, MFA (see ADR-0002) |
| Secrets & config | Secrets Manager + SSM Parameter Store + KMS, via External Secrets + IRSA |
| Edge & TLS | ACM + CloudFront + AWS WAF, ALB/ingress, Route 53 |
| Data | Aurora (Multi-AZ, PITR, KMS) + ElastiCache |
| Supply chain | ECR scan-on-push + Trivy + Syft SBOM + cosign |
| Audit & detection | CloudTrail + GuardDuty + Security Hub + AWS Config + IAM Access Analyzer |
| Observability | CloudWatch logs/metrics/alarms, PrometheusRule, structured audit events |
| Messaging | SQS / SNS / EventBridge for domain events |

Every Terraform module under `infra/terraform/modules/` is the real production form; on floci the
managed ones are gated off with `count = var.floci ? 0 : 1`.

## Status

| Area | State |
|------|-------|
| Security/audit baseline (`security-baseline` module) | **landed** — CloudTrail, GuardDuty, Security Hub, IAM Access Analyzer |
| WAF + ACM edge | planned |
| Cognito-backed OIDC, config-driven from SSM | Cognito present; config-driven planned |
| Edge hardening — security headers, CORS fail-fast, error hygiene | planned |
| Per-tenant + AI rate limits, DynamoDB idempotency | planned |
| Supply chain — Trivy / SBOM / cosign in CI | planned |

Account-level controls (CloudTrail, GuardDuty, Security Hub, Config) are **per-account singletons**;
where `dev` and `prod` share one account they belong to the platform account-baseline owned by
`local-gitops`, not this app.
