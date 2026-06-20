---
name: add-bounded-context
description: >-
  Add a new bounded context to the TODO App as a full DDD vertical slice
  (domain → application → infrastructure → container.py), register it in the root
  ApplicationContainer, add the import-linter contracts, and write its tests.
---

# Skill: Add a Bounded Context

Use this when introducing a new top-level domain (peer to `users`, `tasks`, `ai`). A context owns a
**full vertical slice** and must obey the layering, isolation, and tenancy rules in
`.claude/rules/architecture.md`.

## When NOT to use this

- If the capability belongs inside an existing context, add a use case instead
  (`add-use-case` skill). A new context is justified only by a genuinely separate domain — do not
  create one speculatively (YAGNI).

## Steps

### 1. Scaffold the vertical slice

Create `src/todo_app/contexts/<name>/` with `container.py` as a **sibling** to the layers:

```
contexts/<name>/
├── domain/
│   ├── entities/
│   ├── value_objects/
│   ├── repositories/        # or ports/ for non-persistence interfaces
│   ├── services/
│   └── events/
├── application/
│   ├── commands/
│   ├── queries/
│   └── dto/
├── infrastructure/
│   ├── db/
│   │   ├── models/          # SQLAlchemy models extending shared base_model
│   │   └── repositories/    # implement the domain ports
│   └── mappers/             # entity ↔ ORM model
└── container.py             # <Name>Container (composition root)
```

### 2. Build inside-out (domain first)

1. **Domain** — pure Python entities, value objects, and **interfaces only** for
   repositories/ports. No ORM, no Pydantic, no framework imports.
2. **Application** — `commands/`, `queries/`, `dto/`. Use cases take dependencies via constructor
   injection and depend only on domain interfaces.
3. **Infrastructure** — SQLAlchemy models on the `shared` base model (so they get `tenant_id`,
   soft delete, audit, timestamps), repository implementations, and mappers. If the context is
   tenant-owned, add an RLS policy (next step).

### 3. Tenant isolation (if the context owns data)

- Models extend `shared/infrastructure/db/base_model.py` → inherit `tenant_id`.
- Add an RLS policy under `migrations/policies/<name>_rls.sql`:
  ```sql
  CREATE POLICY tenant_isolation ON <table>
    USING (tenant_id = current_setting('app.tenant_id')::uuid);
  ```
- Add the Atlas migration. Tenancy is enforced by RLS, not app-layer filtering.

### 4. Compose the container

- In `contexts/<name>/container.py`, define `<Name>Container(containers.DeclarativeContainer)`
  wiring the context's repositories, adapters, and use cases as providers. `container.py` is the
  only module allowed to import across all three layers.

### 5. Register in the root ApplicationContainer

In `core/di/container.py`, add the sub-container in dependency order:

```python
<name> = providers.Container(<Name>Container, config=config, shared=shared)
```

If the context depends on another context, pass it explicitly as a read-only port
(e.g. `..., tasks=tasks`) — never via a direct cross-context import. Mirror the existing
`tasks=..., users=...` / `ai=..., tasks=...` pattern.

### 6. Add import-linter contracts

In `pyproject.toml`, extend the contracts so the new context is covered by:

- the **layered** contract (`domain` ↛ `application`/`infrastructure`; `application` ↛
  `infrastructure`; only `container.py` crosses layers), and
- the **independence** contract (the new context cannot import other contexts' internals, and they
  cannot import its internals).

### 7. Presentation (if exposed)

- Add `presentation/api/v1/<name>/{routers.py,serializers.py}` and/or
  `presentation/cli/commands/<name>.py`, calling the application use cases only. Serializers map
  to/from **entities**, never DB models.

### 8. Tests

- `tests/unit/<name>/` — domain + use cases with in-memory fakes (target 100%).
- `tests/integration/<name>/` — repositories against a DB; RLS isolation test if tenant-owned
  (needs Postgres, `TEST_DATABASE_URL`).
- Ensure `tests/architecture/` covers the new context's boundaries.

## Verify

```bash
task check:architecture   # contracts pass (incl. the new context)
task check:quality        # lint, types, dead code, coverage ≥ 97%
task test:unit
```
