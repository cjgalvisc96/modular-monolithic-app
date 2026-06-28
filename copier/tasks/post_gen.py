import sys


def migrate_contexts() -> None:
    pass


COMMANDS = {"migrate-contexts": migrate_contexts}


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"usage: post_gen.py [{'|'.join(COMMANDS)}]", file=sys.stderr)
        return 2
    COMMANDS[sys.argv[1]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
