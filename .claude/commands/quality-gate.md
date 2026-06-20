# Command: quality-gate

Run the full pre-merge gate. This mirrors CI and must pass before any change is merged.

## Run

```bash
task check:quality && task check:architecture && task test:coverage
```

## What each step checks

| Step | Checks |
|------|--------|
| `task check:quality` | ruff (lint/format, line length 100), pyright (types), vulture (dead code), and the coverage gate |
| `task check:architecture` | `import-linter` contracts: layered dependency direction, context isolation, presentation purity, the `container.py` exception |
| `task test:coverage` | Full test run with coverage report; gate is **≥ 97%** |

## Pass criteria

- ruff: no lint errors, formatted.
- pyright: no new type errors.
- vulture: no dead-code findings.
- import-linter: all contracts satisfied (no layer or context-boundary violations).
- coverage: **≥ 97%** overall, and the RLS isolation test passes (requires Postgres via
  `TEST_DATABASE_URL` — see `.claude/rules/testing.md`).

## If it fails

- **Lint/type/dead-code** → fix the code; do not relax ruff/pyright/vulture config to pass.
- **Architecture contract** → the violation is a real boundary break. Fix the imports/structure;
  changing a contract is the Architect's decision and needs an accompanying ADR.
- **Coverage** → add the missing tests; do not lower the threshold.

Do not merge on a red gate. See `docs/development/governance.md` for the rationale.
