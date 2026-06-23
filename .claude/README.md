# Claude Code Harness

This directory configures Claude Code for ongoing AI-assisted development of the TODO App. It
encodes the project's hard rules, reusable skills, and commands so an agent can contribute without
re-deriving the architecture each session.

## Contents

```
.claude/
├── rules/
│   ├── architecture.md     # hard architectural rules (layering, isolation, tenancy, IAM)
│   ├── coding-style.md     # ruff/typing/naming, SOLID/DRY/KISS/YAGNI
│   └── testing.md          # coverage ≥ 97%, fakes for ports, RLS needs Postgres
├── skills/
│   ├── add-bounded-context/SKILL.md   # how to add a new bounded context
│   └── add-use-case/SKILL.md          # how to add a command/query use case
└── commands/
    └── quality-gate.md     # run the full quality + architecture + coverage gate
```

## How it is used

- **Rules** are always-on constraints. Before writing or changing code, an agent reads
  `rules/architecture.md`, `rules/coding-style.md`, and `rules/testing.md` and treats them as
  non-negotiable. They mirror the boundaries enforced by `import-linter` and the quality gate.
- **Skills** are step-by-step procedures for recurring structural tasks (adding a bounded context,
  adding a use case). They keep new code consistent with the existing contexts.
- **Commands** are runnable workflows. `quality-gate` is the pre-merge check that mirrors CI.

## Relationship to the agent harness

The role-based agent team lives under `.agents/` (Lead, Developer, Architect, Tester, DevOps, SRE).
The `.claude/` rules and skills are the concrete conventions those roles enforce — the Architect
owns the architecture rules and import-linter contracts, the Developer follows the skills, and the
Tester owns the testing rule.

## Source of truth

These files summarize and operationalize the design described in the `docs/` site and the root
planning docs (`enterpise-plan.md`, `copier-plan.md`). Where this directory and the design docs ever
disagree, the design docs win and these files should be updated.
