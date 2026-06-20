# Architecture Decision Records

This directory captures the **non-obvious** architectural decisions behind the TODO App — the ones
that would otherwise get re-litigated mid-implementation or quietly reversed by a well-meaning
change. Each ADR records a decision, the context that forced it, and the consequences we accepted.

## The ADR process

- **One decision per record.** ADRs are numbered sequentially and immutable once accepted. If a
  decision changes, write a new ADR that supersedes the old one rather than editing history.
- **Standard format.** Every ADR has: **Title**, **Status**, **Context**, **Decision**, and
  **Consequences**.
- **Status lifecycle.** `Proposed → Accepted → (Superseded by ADR-NNNN)`. All current ADRs are
  **Accepted**.
- **Scope.** ADRs document decisions that are expensive to reverse or that constrain future work
  (tenancy model, identity provider, context boundaries, IAM posture). Routine implementation
  choices do not need an ADR.

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-per-context-di-containers.md) | Per-context DI containers composed by a root `ApplicationContainer` | Accepted |
| [0002](0002-cognito-over-keycloak.md) | AWS Cognito over Keycloak as the identity provider | Accepted |
| [0003](0003-rls-over-app-layer-tenancy.md) | PostgreSQL RLS over application-layer tenant filtering | Accepted |
| [0004](0004-ai-as-bounded-context.md) | AI as its own bounded context behind a port | Accepted |
| [0005](0005-db-init-as-separate-job.md) | Database initialization as a separate Kubernetes Job | Accepted |
| [0006](0006-least-privilege-iam-irsa.md) | Least-privilege IAM with one IRSA role per workload | Accepted |

These records correspond to the cross-cutting decisions log in the repository's `plan.md`.
