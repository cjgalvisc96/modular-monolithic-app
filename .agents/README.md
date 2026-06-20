# Agent Harness

This project uses a **harness engineering** approach: instead of a single assistant, work is carried
out by a small team of role-specialized agents, coordinated by a **Lead**. Each role has a charter
in its `role.md` defining its mission, responsibilities, inputs, outputs, and — importantly — its
**boundaries** (what it must not do).

## The team

| Role | File | Owns |
|------|------|------|
| **Lead** | [`lead/role.md`](lead/role.md) | Coordination, sequencing, final decisions |
| **Developer** | [`developer/role.md`](developer/role.md) | Implementation within the layering/context rules |
| **Architect** | [`architect/role.md`](architect/role.md) | DDD/architecture compliance, import-linter contracts |
| **Tester** | [`tester/role.md`](tester/role.md) | Test pyramid, coverage, RLS isolation |
| **DevOps** | [`devops/role.md`](devops/role.md) | Helm, Terraform/Terragrunt, CI |
| **SRE** | [`sre/role.md`](sre/role.md) | Observability, reliability, on-call |

## How to use the roles

1. **Start with the Lead.** The Lead reads the request, breaks it into tasks, and delegates to the
   relevant role(s). For a single session's first prompt or a complex, high-impact change, the Lead
   may invoke deeper "think longer" reasoning; routine changes rely on project knowledge.
2. **Each role stays in its lane.** A role operates within its charter and respects its boundaries.
   When a task crosses a boundary (e.g. a Developer change that would alter an import-linter
   contract), the role hands off to the owner (here, the Architect) rather than reaching across.
3. **The Architect guards the boundaries.** Any change touching layer direction, context isolation,
   or the `container.py` exception goes through the Architect, who owns the import-linter contracts.
4. **The Tester gates correctness.** No change merges without the test pyramid passing and coverage
   ≥ 97%; the RLS isolation test must pass against real Postgres.
5. **DevOps and SRE own the runtime.** Infrastructure (Helm/Terraform/IRSA) is DevOps; observability
   and reliability are SRE.

## Shared project conventions every role enforces

These are the non-negotiables that bind all roles. They are documented in detail under `docs/` and
in the repository's `plan.md`, `project-structure.md`, and `todo-app-architecture-summary.md`:

- **Dependency direction**: `domain → application → infrastructure`, never reversed. Only
  `container.py` may import across all three layers.
- **Context isolation**: `users`, `tasks`, `ai`, `shared` never import each other's internals;
  cross-context access is via explicit ports wired at the root `ApplicationContainer`.
- **Presentation purity**: `api/` and `cli/` call `application/` use cases only; serializers depend
  on entities, not DB models.
- **Tenancy boundary**: Cognito `tenant_id` claim → `SET LOCAL app.tenant_id` → PostgreSQL RLS. RLS
  is the enforcement boundary, not app-layer filtering.
- **IAM**: one least-privilege IRSA role per workload.
- **Design discipline**: SOLID, DRY, KISS, YAGNI; overengineering is a defect.

The corresponding Claude Code rules live under `.claude/rules/`.
