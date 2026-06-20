# ADR-0001: Per-context DI containers composed by a root ApplicationContainer

## Status

Accepted

## Context

The application is a modular monolith with four bounded contexts (`shared`, `users`, `tasks`,
`ai`). Each context owns a full vertical slice and must remain independently testable and, in
principle, independently extractable. We use `dependency-injector` for IoC.

A naive approach is a single flat container that wires every repository, use case, and adapter
across all contexts. That makes cross-context coupling implicit — any provider can reference any
other — and it erodes context isolation: there is no structural signal of where one context's
boundary ends and another's begins. It also makes a single context hard to instantiate or test in
isolation.

We also had to decide *where* the composition root lives relative to a context's layers. Placing
`container.py` inside `infrastructure/` would visually imply that `application` depends on
`infrastructure`, inverting the dependency rule.

## Decision

Use **two-tier DI composition**:

1. Each context owns its own container — `SharedContainer`, `UsersContainer`, `TasksContainer`,
   `AiContainer` — defined in a `container.py` that sits as a **sibling** to `domain/`,
   `application/`, and `infrastructure/`. Each is independently instantiable and testable.
2. `core/di/container.py` defines a single `ApplicationContainer` that composes the context
   containers via `providers.Container(...)` sub-containers and wires cross-context dependencies
   **explicitly** as sub-container arguments:

   ```python
   shared = providers.Container(SharedContainer, config=config)
   users = providers.Container(UsersContainer, config=config, shared=shared)
   tasks = providers.Container(TasksContainer, config=config, shared=shared, users=users)
   ai = providers.Container(AiContainer, config=config, shared=shared, tasks=tasks)
   ```

`container.py` is the **only** module permitted to import across all three layers of a context;
this exception is enforced by `import-linter`.

## Consequences

- **Positive — visible coupling.** Every cross-context dependency (`tasks → users`, `ai → tasks`)
  appears as an explicit argument at the root, making it reviewable rather than buried in a flat
  container.
- **Positive — isolation preserved.** Each context can be instantiated and unit-tested on its own;
  contexts can be extracted into services later with minimal rewiring.
- **Positive — dependency rule stays honest.** Keeping `container.py` a sibling of the layers
  avoids the inverted-dependency implication of nesting it in `infrastructure/`.
- **Negative — wiring ordering matters.** The container ordering must follow the dependency graph
  (`users` before `tasks`, `tasks` before `ai`); a unit test asserts no provider is left unwired,
  including cross-context bindings.
- **Negative — slight boilerplate.** Each context maintains its own container, but this cost is
  small relative to the isolation it buys.
