# Rule: Architecture

These are hard rules. They are enforced by `import-linter` (`task ensure_architecture`) and
`tests/architecture/`. Do not weaken a contract to make a change pass — fix the change.

## Dependency direction

Within every bounded context (`shared`, `users`, `tasks`, `ai`):

```
domain → application → infrastructure   (never reversed)
```

- `domain/` is pure Python: entities, value objects, repository/port **interfaces**, domain
  services, events. No ORM, no Pydantic, no framework imports.
- `application/` depends only on `domain/` interfaces. Use cases (`commands/`, `queries/`) take
  their dependencies via constructor injection and use DTOs at the boundary.
- `infrastructure/` implements the domain ports: SQLAlchemy models, repositories, mappers, external
  adapters (Cognito for `users`, Bedrock for `ai`).

## Only `container.py` crosses layers

A context's `container.py` is the **only** module permitted to import across all three layers. It
sits as a **sibling** to `domain/`, `application/`, and `infrastructure/` — never nested inside
`infrastructure/`. This is the single explicit exception to the layered contract.

## Context isolation

- `users`, `tasks`, `ai` must **not** import each other's internals. `shared` is the only common
  kernel.
- Cross-context access is via **explicit, read-only ports** wired at the root
  `ApplicationContainer` — `tasks → users` (user lookup) and `ai → tasks` (task read). These are the
  only cross-context edges, and they are uni-directional.
- A `Task` references a `UserId` value object, not a `User` entity, to preserve isolation.

## Presentation purity

- `presentation/api/` and `presentation/cli/` call `application/` use cases only — no business
  logic in routers or CLI commands.
- **Serializers depend on domain entities, never on DB models.** A DB model change must not force an
  API contract change without an explicit mapper update.
- Both API and CLI invoke the *same* command/query classes via the same `ApplicationContainer`.

## Tenancy is RLS, not app-layer filtering

- Tenant context flows: Cognito `tenant_id` claim → tenant-binding middleware →
  `SET LOCAL app.tenant_id` (`shared/infrastructure/db/tenant_context.py`) → PostgreSQL RLS policies
  (`migrations/policies/*.sql`).
- **RLS is the enforcement boundary.** Application-layer `WHERE tenant_id` is defense-in-depth, not
  the source of truth. Never replace RLS with app-layer filtering.

## AI behind a port

- The `ai` context depends on the `LlmClient` port. `boto3`/Bedrock appears **only** in
  `ai/infrastructure/bedrock/bedrock_client.py`. Never call Bedrock from domain or application code,
  or from another context.

## Least-privilege IAM via IRSA

- One scoped IAM role per workload, bound via IRSA: API pod, AI pod (`bedrock:InvokeModel` on
  specific ARNs), DB-init Job (DDL + secret read, no data access), EventBridge publisher
  (publish-only). No shared or account-wide role.

See `docs/architecture/` for the full narrative and `docs/adr/` for the rationale behind each rule.
