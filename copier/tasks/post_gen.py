"""Post-generation helpers invoked by copier `_tasks`.

Kept intentionally small: copier handles file rendering and conditional
inclusion; this only does the few imperative steps copier cannot express
declaratively (e.g. answer-driven migrations across template versions).
"""

import sys


def migrate_contexts() -> None:
    """Placeholder for a `_migrations` step that reshapes answers between
    template major versions. No-op until the first breaking template change."""


COMMANDS = {"migrate-contexts": migrate_contexts}


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"usage: post_gen.py [{'|'.join(COMMANDS)}]", file=sys.stderr)
        return 2
    COMMANDS[sys.argv[1]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
