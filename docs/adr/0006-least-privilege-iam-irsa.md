# ADR-0006: Least-privilege IAM with one IRSA role per workload

## Status

Accepted

## Context

The application runs several distinct workloads on EKS: the API pod, the AI/Bedrock pod, the
DB-init Job, and an EventBridge publisher. Each needs different AWS permissions — database access,
Bedrock invocation, DDL execution, event publishing.

A shared or account-wide execution role is operationally simple but dangerous: any single
compromised pod inherits the union of all permissions, so the blast radius of a breach equals the
entire application's AWS footprint. It also makes least-privilege review impossible — there is no
per-workload policy to audit.

## Decision

Grant **one least-privilege IAM role per workload**, bound to that workload's Kubernetes
ServiceAccount via **IRSA** (IAM Roles for Service Accounts). The roles are defined as discrete
Terraform modules under `infra/terraform/modules/iam/`, reviewed independently of the resources
they grant access to:

- **API pod role** — Aurora access via IAM database authentication and read-only access to its
  specific Secrets Manager secrets. No Bedrock, no DDL.
- **AI pod role** — `bedrock:InvokeModel` only, scoped to specific model ARNs. No S3, no broader
  Bedrock permissions.
- **DB-init Job role** — schema/DDL execution and Secrets Manager read only; explicitly no runtime
  access to application data tables (see [ADR-0005](0005-db-init-as-separate-job.md)).
- **EventBridge-publishing role** — publish-only to a specific event bus; no subscribe or manage
  permissions.

The Helm service accounts (`infra/k8s/helm/templates/service-account.yaml`) are IRSA-annotated to
bind each pod to its scoped role.

## Consequences

- **Positive — contained blast radius.** A compromised pod can only do what that workload needs; a
  breached AI pod cannot touch the database or read arbitrary secrets.
- **Positive — auditable.** Each role is a small, independently reviewable Terraform module; Trivy
  scans confirm no role grants broader-than-scoped permissions.
- **Positive — defense-in-depth with tenancy.** Even within the database, RLS (see
  [ADR-0003](0003-rls-over-app-layer-tenancy.md)) scopes data by tenant; IAM scopes by workload.
- **Negative — more roles to maintain.** Every new workload needs its own role and service account,
  which is more Terraform than a single shared role — accepted as the cost of least privilege.
- **Negative — IRSA setup required.** The cluster must have the OIDC provider and trust
  relationships configured for IRSA to function.
