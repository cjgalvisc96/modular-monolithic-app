"""Typer CLI entrypoint for operational/admin commands."""

import typer

from todo_app.presentation.cli.commands import ai, tasks, users

app = typer.Typer(help="TODO app admin/operational CLI.", no_args_is_help=True)
app.add_typer(users.app, name="users")
app.add_typer(tasks.app, name="tasks")
app.add_typer(ai.app, name="ai")


if __name__ == "__main__":  # pragma: no cover
    app()
