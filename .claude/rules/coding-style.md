# Rule: Coding Style

Enforced by `task check:quality` (ruff, pyright, vulture). Style is checked, not optional.

## Formatting & imports

- **ruff** for linting and formatting; **line length 100**.
- Imports sorted by `ruff.lint.isort`. No unused imports.

## Typing

- Type hints on public functions and methods. **pyright** must pass with no new errors.
- Prefer precise types (value objects, enums, `Literal`) over bare `str`/`int` where the domain has
  a real type.

## Naming

- Modules and packages: `snake_case`. Classes: `PascalCase`. Functions/variables: `snake_case`.
- Use case classes are named for their intent: `CreateTaskCommand`, `ListTasksQuery`,
  `GenerateTaskSuggestionCommand`.
- Ports/interfaces read as capabilities: `UserRepository`, `TaskRepository`, `LlmClient`.

## Dead code

- **vulture** must not flag unreferenced code. Delete dead code rather than commenting it out.

## Design discipline — SOLID, DRY, KISS, YAGNI

- Apply established patterns (builder, ports & adapters, CQRS, DI) only where they remove **real**
  coupling or duplication.
- **Do not add abstraction, indirection, or a pattern for a hypothetical future need.**
  Overengineering and unnecessary indirection are treated as **defects**, not sophistication.
- Prefer the simplest arrangement that satisfies the present requirement. If a function does the job
  of a class, write the function.
- Single Responsibility: a module/class/use case does one thing. Dependency Inversion: depend on the
  port, not the concrete adapter.

## Practical guidance

- Constructor-inject dependencies (repositories, ports) — never instantiate an adapter inside a use
  case.
- Keep DTOs (application boundary) and serializers (HTTP boundary) as distinct objects that map
  cleanly, not the same class.
- Keep `domain/` free of framework concerns; if you reach for SQLAlchemy or Pydantic in `domain/`,
  it belongs in `infrastructure/` or the serializer layer instead.
