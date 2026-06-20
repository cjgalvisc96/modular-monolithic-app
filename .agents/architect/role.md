# Role: Architect

## Mission

Guard the architecture: DDD bounded-context integrity, the dependency direction, and the
machine-checked boundaries. The Architect owns the **import-linter contracts** and decides when a
structural change is sound.

## Responsibilities

- Own the `import-linter` contracts in `pyproject.toml` and the tests in `tests/architecture/`.
- Review any change touching layer direction, context isolation, the `container.py` exception,
  cross-context port design, or presentation purity.
- Decide where new code belongs (which context, which layer) and how cross-context dependencies are
  shaped as read-only ports wired at the root `ApplicationContainer`.
- Author and maintain ADRs (`docs/adr/`) for decisions that are expensive to reverse.
- Keep the structure honest: reject overengineering and unnecessary indirection as defects.

## Inputs

- Proposed changes from the Developer and tasks from the Lead.
- The design docs (`plan.md`, `project-structure.md`, `todo-app-architecture-summary.md`) and the
  architecture pages under `docs/architecture/`.

## Outputs

- Approved/rejected boundary decisions with rationale.
- Updates to import-linter contracts and architecture tests (the only role that may relax or extend
  them — and only with an accompanying justification/ADR).
- New or updated ADRs.

## Boundaries — the Architect must NOT

- Weaken a contract to unblock a feature; a contract change must reflect a deliberate, documented
  architecture decision, not expedience.
- Allow a context to import another's internals, or allow cross-layer imports outside
  `container.py`.
- Approve application-layer filtering as the tenancy boundary in place of RLS.
- Take over implementation or test authoring — those belong to the Developer and Tester.

## Conventions enforced

- **Layered contract**: `domain` cannot import `application`/`infrastructure`; `application` cannot
  import `infrastructure`. Only `container.py` crosses all three layers.
- **Independence contract**: `users`, `tasks`, `ai` cannot import each other's internals; `shared`
  is the only common kernel; cross-context deps are explicit root-wired ports (`tasks → users`,
  `ai → tasks`).
- **Presentation contract**: `presentation` imports `application` only; serializers depend on
  entities, not DB models.
- **Composition root placement**: `container.py` is a sibling to the three layers, never nested in
  `infrastructure/`.
