# Governance

Code quality and architectural integrity are enforced by tooling, not by review convention alone.
The pipelines below run via `task ensure_quality` and `task ensure_architecture` and gate every
change.

## Tooling

| Tool | Role | Configuration |
|------|------|---------------|
| **ruff** | Linting and import sorting (`ruff.lint.isort`); line length 100 | `pyproject.toml` |
| **pyright** | Static type checking | `pyproject.toml` |
| **vulture** | Dead-code detection | `pyproject.toml` |
| **import-linter** | Architectural boundary enforcement (layers + context isolation) | `pyproject.toml` |
| **pytest** | Test execution + coverage gate (≥ 97%) | see [Testing](testing.md) |

Dependencies are managed with **uv** and grouped into `prod`, `dev`, `lint`, and `test` in
`pyproject.toml`.

## Quality gate

```bash
task ensure_quality
```

Runs ruff, pyright, and vulture, and enforces the coverage gate. Code style expectations:

- **Line length 100**, ruff-formatted, imports sorted by `ruff.lint.isort`.
- **Type hints** on public functions; pyright must pass with no new errors.
- **No dead code** — vulture must not flag unreferenced code.
- **SOLID, DRY, KISS, YAGNI** — abstraction is added to solve a present problem, never a
  hypothetical one. Overengineering and unnecessary indirection are treated as defects.

## Architecture gate

```bash
task ensure_architecture
```

Runs the `import-linter` contracts (also exercised by `tests/architecture/`). The contracts encode
the system's hard rules:

- **Layered contract (per context)** — `domain` cannot import `application` or `infrastructure`;
  `application` cannot import `infrastructure`. Dependencies point inward only. See
  [Layering](../architecture/layering.md).
- **Independence contract (between contexts)** — `users`, `tasks`, and `ai` cannot import each
  other's internals. Only the `shared` kernel is a permitted common dependency. Cross-context
  access goes through explicit ports wired at the root. See
  [Bounded Contexts](../architecture/bounded-contexts.md).
- **Presentation contract** — `presentation` may import `application` (and domain types for
  serialization) but not `infrastructure` or DB models. Serializers depend on **entities, not DB
  models**.
- **The `container.py` exception** — only `container.py` modules may import across all three layers
  of a context. This is the single, explicit exception to the layered contract.

Because these contracts are machine-checked on every run, the boundaries cannot silently erode as
the codebase grows — which is exactly the failure mode a modular monolith is most prone to.

## CI

CI runs the same gates a developer runs locally. A change must pass
`task ensure_quality && task ensure_architecture && task coverage` to merge. The Claude harness
bundles this as the `quality-gate` command (`.claude/commands/quality-gate.md`).
