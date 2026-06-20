# ADR-0005: Database initialization as a separate Kubernetes Job

## Status

Accepted

## Context

The application runs database schema migrations (Atlas) and initialization. In Kubernetes, the API
runs as a `Deployment` with **multiple replicas**. We had to decide where migrations run.

Running migrations from API container startup means every replica races to apply the same
migrations on boot. This causes lock contention, repeated/duplicate migration attempts, slower and
flakier rollouts, and a startup path whose success depends on DB DDL completing — coupling
application availability to schema changes. It also means the API pod's IAM role would need DDL
privileges it otherwise does not need.

## Decision

Run database initialization and migrations as a **separate Kubernetes `Job`**, decoupled from the
API `Deployment`. The Job is defined at `infra/k8s/helm/templates/job-db-init.yaml` and run via a
Helm hook (`pre-install` / `pre-upgrade`) so it completes **before** API pods report ready. The
Job runs under its own service account and IRSA role limited to DDL execution and Secrets Manager
read — with no runtime access to application data tables (see
[ADR-0006](0006-least-privilege-iam-irsa.md)).

## Consequences

- **Positive — no migration races.** Exactly one Job applies migrations once, regardless of API
  replica count; no lock contention or duplicate attempts.
- **Positive — ordered rollouts.** The Helm hook guarantees migrations finish before the new API
  version serves traffic.
- **Positive — least privilege.** The API pod role never needs DDL privileges; DDL is isolated to
  the Job's role.
- **Negative — orchestration to manage.** The Job must succeed for an install/upgrade to proceed; a
  failed migration blocks the rollout (which is the correct fail-closed behavior but requires
  operational attention).
- **Negative — Helm hook semantics.** Migrations are coupled to the Helm release lifecycle; manual
  or out-of-band migration runs must be handled deliberately.
