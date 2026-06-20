# ADR-0002: AWS Cognito over Keycloak as the identity provider

## Status

Accepted

## Context

The application needs an identity provider for authentication (JWT issuance), SSO, and the delivery
of multi-tenancy claims (`tenant_id`) and role/group claims into every token. The system is
deployed on AWS (EKS, Aurora, Bedrock), so the identity provider must integrate cleanly with the
rest of the cloud infrastructure and be operable by the same team.

Keycloak is a capable open-source IdP, but running it means operating a stateful service: its own
deployment, database, upgrades, availability, and backups — a second piece of identity
infrastructure to maintain alongside the application. We needed to weigh that operational surface
against a managed AWS-native option.

## Decision

Use **AWS Cognito** as the single source of truth for authentication and SSO, replacing Keycloak.
A single Cognito User Pool serves the whole application. A **pre-token-generation Lambda** injects
the `tenant_id` custom claim and role/group claims into every issued JWT. The Cognito resources are
defined as a Terraform module (`infra/terraform/modules/cognito/`), and the application-side
integration (JWKS fetch + cache, claim extraction) lives in `users/infrastructure/auth/`.

No Keycloak or other IdP is deployed.

## Consequences

- **Positive — one IdP across app and infra.** The same provider backs application-level auth and
  the cloud infrastructure; identity is defined as code in the same Terraform tree as the rest of
  the platform.
- **Positive — no IdP to operate.** Cognito is managed; there is no Keycloak deployment, database,
  or upgrade burden.
- **Positive — claims at mint time.** The pre-token Lambda guarantees `tenant_id` and role claims
  are present in every token, which the tenancy chain (see
  [ADR-0003](0003-rls-over-app-layer-tenancy.md)) and authorization both depend on.
- **Negative — AWS coupling.** Identity is now tied to AWS; a multi-cloud or on-prem deployment
  would require revisiting this decision.
- **Negative — Cognito constraints.** Cognito's customization model is less flexible than
  Keycloak's; non-standard flows must fit Cognito's primitives (pre-token Lambda, groups,
  triggers).
